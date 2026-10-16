"""Calibração offline do Risk rationale checker v2 (Amendment 11), só com development.

O checker v1 (blob ``7636ad26``, congelado no development v3) marcava como
``VERDICT_TEXT_CONTRADICTION`` duas aprovações que negam o veto fora da janela
de 30 caracteres ("Não há fatores adversos ... que justifiquem veto"). O v2 decide
a polaridade por construção na sentença. Este script:

1. monta o corpus dourado: toda resposta ÚNICA do Risk LLM da evidência já
   consumida (v1, v2, CAL-B1 — sem chamada de Risk —, CAL-B2, Hardening/B0,
   CAL-A, Sequential, Stress, development v3) + casos sintéticos PT/EN rotulados;
2. aplica o v1 (lido do blob git, não do arquivo atual) e o v2;
3. exige os critérios de aceitação antes de qualquer chamada CAL-B3;
4. reaplica o v2 offline ao corpus v3 (nada é rerodado live).

Nenhuma data CAL-B3 é lida. Nenhuma chamada ao provedor.

Uso: ``python scripts/risk_checker_v2_calibration.py`` ->
``docs/evidence/h2_v3/risk_checker_v2/{golden_corpus,calibration_report}.json``.
"""

import hashlib
import json
import subprocess
import sys
import types
from collections import Counter
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

from h2_v3_summary import phases  # noqa: E402

from src.agents import risk_contract as v2  # noqa: E402
from src.agents.llm_trace import load_trace  # noqa: E402
from src.experiments import anchors  # noqa: E402

OUT = ROOT / "docs" / "evidence" / "h2_v3" / "risk_checker_v2"
V1_BLOB = "7636ad26e3ed7777c38d532e2ab4267f268359de"  # risk_contract.py do development v3 (c148dc7)
VTC = v2.VERDICT_TEXT_CONTRADICTION
#: Os dois falsos positivos registrados no development v3 (Registro de execução).
KNOWN_FALSE_POSITIVES = {
    ("v3 Hardening", "2002-04-19"): "Não há fatores adversos nas métricas fornecidas que justifiquem veto",
    ("v3 Stress", "2018-09-10"): "sem violação de limites ou condições adversas que justifiquem veto",
}
#: Payload lógico do Risk na âncora CAL-B2 2023-06-26 (consumida, development).
PAYLOAD = {"risk_metrics": {"current_concentration": 0.0, "current_drawdown": 0.0, "recent_volatility": 0.364617},
           "technical_signal": {"confidence": 0.462, "justification": "Consenso coletivo: 3/5 votos em COMPRA",
                                "signal": "COMPRA"}}
V = "volatilidade recente de 36.46%"
#: (categoria, veredito, texto, contradição esperada). Todo texto cita a métrica
#: do payload e nenhuma regra numérica: só VERDICT_TEXT_CONTRADICTION está em jogo.
SYNTHETIC = [
    # negação que APOIA o veredito (não é contradição)
    ("PT_NEGATION_SUPPORTS_VERDICT", "APROVADO", f"Não há fatores adversos nas métricas fornecidas que justifiquem veto; {V}.", False),
    ("PT_NEGATION_SUPPORTS_VERDICT", "APROVADO", f"A {V} e o drawdown nulo não justificam veto.", False),
    ("PT_NEGATION_SUPPORTS_VERDICT", "APROVADO", f"Com {V}, as métricas não justificam o veto da operação.", False),
    ("PT_NEGATION_SUPPORTS_VERDICT", "APROVADO", f"Com {V}, não há motivo para veto.", False),
    ("PT_NEGATION_SUPPORTS_VERDICT", "APROVADO", f"A {V} não recomenda veto.", False),
    ("PT_NEGATION_SUPPORTS_VERDICT", "APROVADO", f"Sem qualquer razão para vetar, dada a {V}.", False),
    ("PT_NEGATION_SUPPORTS_VERDICT", "APROVADO", f"Não existem razões, nas métricas fornecidas, para veto; {V}.", False),
    ("PT_NEGATION_SUPPORTS_VERDICT", "APROVADO", f"Nada no payload recomenda veto: {V} e drawdown nulo.", False),
    ("PT_NEGATION_SUPPORTS_VERDICT", "APROVADO", f"A {V} foi assimilada sem veto e o drawdown é nulo.", False),
    ("PT_NEGATION_SUPPORTS_VERDICT", "APROVADO", f"As métricas não indicam riscos que justifiquem o veto; {V}.", False),
    ("PT_NEGATION_SUPPORTS_VERDICT", "VETADO", f"Não há condições para aprovação com {V} e consenso dividido.", False),
    ("PT_NEGATION_SUPPORTS_VERDICT", "VETADO", f"A operação não pode ser aprovada com {V}.", False),
    ("EN_NEGATION_SUPPORTS_VERDICT", "APROVADO", f"There is no reason to veto: {V} and zero drawdown.", False),
    ("EN_NEGATION_SUPPORTS_VERDICT", "APROVADO", f"No compelling reason to veto given {V}.", False),
    ("EN_NEGATION_SUPPORTS_VERDICT", "APROVADO", f"The {V} does not justify a veto.", False),
    ("EN_NEGATION_SUPPORTS_VERDICT", "APROVADO", f"The {V} does not, by itself, justify a veto.", False),
    ("EN_NEGATION_SUPPORTS_VERDICT", "APROVADO", f"Nothing in the payload warrants a veto; {V}.", False),
    ("EN_NEGATION_SUPPORTS_VERDICT", "VETADO", f"The trade should not be approved with {V}.", False),
    # contradição genuína (texto declara o veredito oposto ou nega o próprio)
    ("PT_TRUE_CONTRADICTION", "APROVADO", f"Há fatores que justificam veto: {V}.", True),
    ("PT_TRUE_CONTRADICTION", "APROVADO", f"Não há condições para aprovação com {V}.", True),
    ("PT_TRUE_CONTRADICTION", "APROVADO", f"A entrada é vetada; {V}.", True),
    ("PT_TRUE_CONTRADICTION", "VETADO", f"Operação aprovada: {V} aceitável.", True),
    ("PT_TRUE_CONTRADICTION", "VETADO", f"Não há motivo para veto: {V}.", True),
    ("PT_TRUE_CONTRADICTION", "APROVADO", f"Não existem razões para aprovar com {V}.", True),
    ("PT_TRUE_CONTRADICTION", "APROVADO", f"Não há drawdown, o que justifica veto diante da {V}.", True),
    ("PT_TRUE_CONTRADICTION", "APROVADO", f"Sem drawdown, há fatores que justificam veto: {V}.", True),
    ("PT_TRUE_CONTRADICTION", "APROVADO", f"Não há drawdown, mas há fatores que justificam veto: {V}.", True),
    ("EN_TRUE_CONTRADICTION", "APROVADO", f"The {V} means there are grounds to veto.", True),
    ("EN_TRUE_CONTRADICTION", "APROVADO", f"The {V} leaves no room for approval.", True),
    ("EN_TRUE_CONTRADICTION", "VETADO", f"Trade approved: {V} is acceptable.", True),
    # menção à camada determinística ou concessão: não é veredito deste estágio
    ("HARD_RULE_REFERENCE", "APROVADO", f"As regras duras de veto não foram acionadas; {V} aceitável.", False),
    ("HARD_RULE_REFERENCE", "APROVADO", f"Os filtros determinísticos não vetaram e a {V} é aceitável.", False),
    ("HARD_RULE_REFERENCE", "VETADO", f"Embora a operação tenha sido aprovada pelas regras duras, a {V} leva ao veto.", False),
    ("CONCESSIVE", "VETADO", f"Embora não haja motivo para veto pela concentração, a {V} é elevada; operação vetada.", False),
    # aprovação/veto sem menção problemática
    ("PT_PLAIN_VERDICT", "APROVADO", f"A ausência de exposição e a {V} permitem a aprovação.", False),
    ("PT_PLAIN_VERDICT", "APROVADO", f"A {V} não é baixa e a convicção justifica aprovação.", False),
    ("PT_PLAIN_VERDICT", "VETADO", f"Consenso dividido e {V} elevada: operação vetada para preservar capital.", False),
]


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def git(*args: str) -> str:
    return subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True, check=True,
                          encoding="utf-8").stdout


def checker_v1() -> types.ModuleType:
    """O checker do development v3, executado a partir do blob git (não do arquivo atual)."""
    module = types.ModuleType("risk_contract_v1")
    exec(compile(git("cat-file", "-p", V1_BLOB), "risk_contract_v1.py", "exec"), module.__dict__)
    return module


def codes(module: types.ModuleType, item: dict[str, Any]) -> list[str]:
    return sorted({a["code"] for a in module.audit_risk_rationale(item["analysis"], item["verdict"], item["payload"])})


def development_items() -> list[dict[str, Any]]:
    """Respostas únicas do Risk LLM (identidade + resposta do provedor), primeira fase em que aparecem."""
    seen: dict[tuple[str, str | None], dict[str, Any]] = {}
    for phase, data in phases().items():
        for path in data["risk_traces"]:
            for r in load_trace(path.read_bytes()):
                key = (r.request.identity_digest, r.provider_response_id)
                if r.request.stage != "risk_manager" or r.status != "ok" or key in seen:
                    continue
                seen[key] = {"source": phase, "decision_session": r.request.decision_session, "call_id": r.call_id,
                             "identity_digest": r.request.identity_digest,
                             "risk_system_prompt_sha256": r.request.system_prompt_sha256,
                             "verdict": r.validated_response["verdict"],
                             "analysis": r.validated_response["analysis"], "payload": json.loads(r.request.user_prompt)}
    return list(seen.values())


def label(item: dict[str, Any], v1_codes: list[str]) -> dict[str, Any]:
    """Rótulo do item real: VTC por leitura; R1/R2/CONFIDENCE_ONLY = achados congelados do v1."""
    known = KNOWN_FALSE_POSITIVES.get((item["source"], item["decision_session"]))
    if known is not None and known in item["analysis"]:
        return {"category": "KNOWN_FALSE_POSITIVE_V1", "expected_codes": [c for c in v1_codes if c != VTC],
                "label_basis": "distant negation of veto supporting APROVADO; registered as checker false positive"}
    if any(c != VTC for c in v1_codes):
        return {"category": "FROZEN_INVALID_V1", "expected_codes": v1_codes,
                "label_basis": "frozen v1 V3-R1/R2/R3 finding (Amendment 10 calibration); regression lock"}
    return {"category": f"DEVELOPMENT_{'APPROVAL' if item['verdict'] == 'APROVADO' else 'VETO'}", "expected_codes": [],
            "label_basis": "no genuine verdict/text contradiction on reading; v1 finding set empty "
                           "(regression lock for R1/R2/CONFIDENCE_ONLY, not a recall claim)"}


def main() -> None:
    v1 = checker_v1()
    items = []
    for n, item in enumerate(development_items(), 1):
        v1_codes = codes(v1, item)
        items.append({"id": f"dev-{n:04d}", **item, **label(item, v1_codes), "v1_codes": v1_codes})
    for n, (category, verdict, text, contradiction) in enumerate(SYNTHETIC, 1):
        item = {"id": f"syn-{n:03d}", "source": "synthetic", "verdict": verdict, "analysis": text, "payload": PAYLOAD,
                "category": category, "expected_codes": [VTC] if contradiction else [],
                "label_basis": "constructed PT/EN case with known polarity"}
        items.append({**item, "v1_codes": codes(v1, item)})
    sessions = {i.get("decision_session") for i in items}
    assert not sessions & set(anchors.CAL_B3_ANCHORS), "CAL-B3 date in the development corpus"

    corpus = {"kind": "RISK_RATIONALE_CHECKER_GOLDEN_CORPUS", "checker_version": v2.RISK_RATIONALE_CHECKER_VERSION,
              "scope": "development evidence only (v1, v2, CAL-B1, CAL-B2, Hardening/B0, CAL-A, Sequential, "
                       "Stress, development v3) + synthetic; CAL-B3 never read",
              "items": items}
    OUT.mkdir(parents=True, exist_ok=True)
    corpus_bytes = (json.dumps(corpus, indent=1, ensure_ascii=False) + "\n").encode("utf-8")
    (OUT / "golden_corpus.json").write_bytes(corpus_bytes)

    results = [{**i, "v2_codes": codes(v2, i)} for i in items]
    real = [r for r in results if r["source"] != "synthetic"]
    mismatches = [{k: r[k] for k in ("id", "category", "verdict", "analysis", "expected_codes", "v2_codes")}
                  for r in results if r["v2_codes"] != r["expected_codes"]]

    def flagged(rows: list[dict[str, Any]], key: str, code: str) -> set[str]:
        return {r["id"] for r in rows if code in r[key]}

    preserved = {code: flagged(real, "v1_codes", code) == flagged(real, "v2_codes", code)
                 for code in (v2.UNSUPPORTED_CONFIDENCE_THRESHOLD, v2.UNSUPPORTED_NUMERIC_RULE,
                              v2.CONFIDENCE_ONLY_DECISION)}
    known = [r for r in results if r["category"] == "KNOWN_FALSE_POSITIVE_V1"]
    frozen = [r for r in results if r["category"] == "FROZEN_INVALID_V1"]
    acceptance = {
        "known_false_positives": len(known),
        "known_false_positives_remaining": sum(VTC in r["v2_codes"] for r in known),
        "frozen_invalid_cases": len(frozen),
        "frozen_invalid_regressions": sum(r["v2_codes"] != r["expected_codes"] for r in frozen),
        "V3-R1_preserved": preserved[v2.UNSUPPORTED_CONFIDENCE_THRESHOLD],
        "V3-R2_preserved": preserved[v2.UNSUPPORTED_NUMERIC_RULE],
        "CONFIDENCE_ONLY_DECISION_preserved": preserved[v2.CONFIDENCE_ONLY_DECISION],
        "VERDICT_TEXT_CONTRADICTION_corrected": not any(VTC in r["v2_codes"] for r in known)
        and all((VTC in r["v2_codes"]) == (VTC in r["expected_codes"]) for r in results),
        "corpus_mismatches": len(mismatches),
    }
    acceptance["pass"] = (acceptance["known_false_positives"] == 2 and not acceptance["known_false_positives_remaining"]
                          and not acceptance["frozen_invalid_regressions"] and all(preserved.values())
                          and acceptance["VERDICT_TEXT_CONTRADICTION_corrected"] and not mismatches)

    def confusion(rows: list[dict[str, Any]], key: str) -> dict[str, int]:
        pairs = Counter((VTC in r["expected_codes"], VTC in r[key]) for r in rows)
        return {"true_positive": pairs[True, True], "false_positive": pairs[False, True],
                "false_negative": pairs[True, False], "true_negative": pairs[False, False]}

    by_category = {c: {"items": sum(r["category"] == c for r in results),
                       "v1_vtc": sum(VTC in r["v1_codes"] for r in results if r["category"] == c),
                       "v2_vtc": sum(VTC in r["v2_codes"] for r in results if r["category"] == c)}
                   for c in sorted({r["category"] for r in results})}
    gates = ("V3-R1", "V3-R2", "V3-R3")
    reapplied = {}
    for phase in sorted({r["source"] for r in real if r["source"].startswith("v3")}):
        rows = [r for r in real if r["source"] == phase]
        reapplied[phase] = {"risk_llm_responses": len(rows), "verdicts": dict(Counter(r["verdict"] for r in rows)),
                            **{f"{ver}_{g}": sum(any(v2.GATE_OF[c] == g for c in r[f"{ver}_codes"]) for r in rows)
                               for ver in ("v1", "v2") for g in gates}}
    report = {
        "kind": "RISK_RATIONALE_CHECKER_V2_CALIBRATION",
        "instrument_change_only": "treatment version, Risk prompt, model, spec and system responses unchanged; "
                                  "no live rerun",
        "checker_version": v2.RISK_RATIONALE_CHECKER_VERSION,
        "checker_v1_blob": V1_BLOB,
        "checker_v2_blob": git("hash-object", "src/agents/risk_contract.py").strip(),
        "calibration_script_blob": git("hash-object", "scripts/risk_checker_v2_calibration.py").strip(),
        "golden_corpus_sha256": sha256(corpus_bytes),
        "corpus": {"items": len(results), "development": len(real), "synthetic": len(results) - len(real),
                   "development_verdicts": dict(Counter(r["verdict"] for r in real)),
                   "development_sources": dict(Counter(r["source"].split()[0] for r in real))},
        "verdict_text_contradiction_confusion": {"v1": confusion(results, "v1_codes"),
                                                 "v2": confusion(results, "v2_codes")},
        "by_category": by_category,
        "acceptance": acceptance,
        "mismatches": mismatches,
        "v3_development_offline_reapplication": reapplied,
        "v3_development_offline_totals": {f"{ver}_{g}": sum(p[f"{ver}_{g}"] for p in reapplied.values())
                                          for ver in ("v1", "v2") for g in gates},
        "known_ceiling": "negation scope closes only at an affirmed predicate (há/é/foi...), adversative or "
                         "sentence boundary; 'Com drawdown nulo e sem concentração há fatores...' style "
                         "prefixes and double negation are not resolved",
        "cal_b3_dates_read": 0,
    }
    (OUT / "calibration_report.json").write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n",
                                                 encoding="utf-8", newline="\n")
    print(json.dumps({k: report[k] for k in ("checker_version", "checker_v2_blob", "golden_corpus_sha256", "corpus",
                                             "verdict_text_contradiction_confusion", "acceptance",
                                             "v3_development_offline_totals")}, indent=1, ensure_ascii=False))
    if not acceptance["pass"]:
        print(json.dumps(mismatches, indent=1, ensure_ascii=False))
        sys.exit("checker v2 does not meet the acceptance criteria")


if __name__ == "__main__":
    main()
