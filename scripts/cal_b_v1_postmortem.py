"""Post-mortem da CAL-B v1 (CAL-B1 CONSUMED — NOW DEVELOPMENT EVIDENCE).

Diagnóstico mecânico do excesso de MANTER do Technical v1, só a partir dos
artefatos selados da CAL-B consumida e dos artefatos já publicados das fases
anteriores. Nenhuma chamada ao provedor, nenhum preço posterior a ``t``,
nenhum retorno, nenhuma mudança de configuração, prompt ou código científico.

Uso: ``python scripts/cal_b_v1_postmortem.py`` -> ``docs/evidence/cal_b_v1/postmortem/``.
"""

import json
import re
import statistics
import sys
from collections import Counter
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

from run_cal_b import history_until, load_frame, verify_seal  # noqa: E402

from src.agents.llm_trace import load_trace  # noqa: E402
from src.experiments.anchors import CAL_B_ANCHORS  # noqa: E402
from src.strategies.indicator_family_control import IndicatorFamilyControlParticipant  # noqa: E402

RUN = ROOT / "docs" / "evidence" / "cal_b" / "run_20261005T021523Z"
OUT = ROOT / "docs" / "evidence" / "cal_b_v1" / "postmortem"
LABEL = "CAL-B1 CONSUMED — NOW DEVELOPMENT EVIDENCE"
SIGNALS = ("COMPRA", "VENDA", "MANTER")

#: Taxonomia descritiva por regra textual (múltiplos rótulos; texto preservado).
TAXONOMY = {
    "MIXED_SIGNALS": r"mist|divergen|conflit|contradit|amb[ií]gu|sinais opostos|n[ãa]o h[áa] (?:um )?consenso",
    "INSUFFICIENT_CONFIRMATION": r"confirma[çc][ãa]o|n[ãa]o confirma|sem [^.]{0,25}confirmad|aguard",
    "NEUTRAL_INDICATORS": r"neutr|lateral|indefini|sem dire[çc][ãa]o|sem tend[êe]ncia|consolida",
    "OVERBOUGHT_OVERSOLD_CONFLICT": r"sobrecompr|sobrevend|exaust",
    "GENERIC_UNCERTAINTY": r"incert|cautel|prud[êe]n|indecis|d[úu]vid",
}
TREND = r"tend[êe]ncia|m[ée]dia|sma"
MOMENTUM = r"macd|momentum|rsi|for[çc]a"
CONTRAST = r"embora|por[ée]m|entretanto|contudo|no entanto|apesar|mas\b|enquanto|todavia"
#: Linguagem de MANTER como default de segurança/incerteza. Não inclui "risco de
#: correção" (argumento direcional) nem "neutro" (visão neutra declarada).
DEFAULT_LANGUAGE = (r"cautel", r"prud[êe]n", r"aguard", r"esperar", r"confirma[çc][ãa]o", r"incert", r"evitar",
                    r"seguran[çc]a")
#: Visão genuinamente neutra declarada.
NEUTRAL_VIEW = (r"neutr", r"consolida", r"lateral", r"sem gatilho", r"aus[êe]ncia de gatilho")


#: Afirmação de que o preço está/rompeu ACIMA da banda superior. Verdadeira só
#: com ``bb_upper_gap = close/upper - 1 > 0``; com gap < 0 é leitura errada do
#: dado fornecido (o preço está abaixo da banda superior).
UPPER_BREACH_CLAIM = r"(acima|ultrapass|romp)[^.;,]{0,45}superior"


def labels(text: str) -> list[str]:
    found = [name for name, pattern in TAXONOMY.items() if re.search(pattern, text, re.IGNORECASE)]
    if all(re.search(p, text, re.IGNORECASE) for p in (TREND, MOMENTUM, CONTRAST)):
        found.append("TREND_MOMENTUM_CONFLICT")
    return found or ["OTHER"]


def snippets(text: str, patterns: tuple[str, ...]) -> list[str]:
    out = []
    for pattern in patterns:
        for m in re.finditer(pattern, text, re.IGNORECASE):
            out.append(text[max(0, m.start() - 40): m.end() + 40].strip())
    return out


def sign(x: float) -> str:
    return "+" if x > 0 else "-" if x < 0 else "0"


def stats(values: list[float]) -> dict[str, Any]:
    if not values:
        return {"n": 0}
    return {"n": len(values), "mean": round(statistics.fmean(values), 4), "median": statistics.median(values),
            "min": min(values), "max": max(values)}


def majority(votes: list[str]) -> str:
    """Maioria estrita (> metade) sobre os votos dados; senão NO_MAJORITY."""
    top, count = Counter(votes).most_common(1)[0]
    return top if count > len(votes) / 2 else "NO_MAJORITY"


def feature_signs(f: dict[str, float]) -> dict[str, Any]:
    upper, lower = f["bb_upper_gap"], f["bb_lower_gap"]
    band = "ABOVE_UPPER" if upper > 0 else "BELOW_LOWER" if lower < 0 else "INSIDE"
    # %B descritivo, derivado das duas razões: close/upper = 1+u, close/lower = 1+l.
    lo, up = 1 / (1 + lower), 1 / (1 + upper)
    rsi = f["rsi"]
    return {
        "sma50_gap": sign(f["sma50_gap"]), "sma200_gap": sign(f["sma200_gap"]),
        "bollinger_position": band, "bollinger_percent_b": round((1 - lo) / (up - lo), 4),
        "rsi": rsi, "rsi_zone": "OVERSOLD(<30)" if rsi < 30 else "OVERBOUGHT(>70)" if rsi > 70 else
        ("NEUTRAL_UPPER(50-70)" if rsi >= 50 else "NEUTRAL_LOWER(30-50)"),
        "macd_ratio": sign(f["macd_ratio"]), "macd_signal_ratio": sign(f["macd_signal_ratio"]),
        "macd_minus_signal": sign(f["macd_ratio"] - f["macd_signal_ratio"]),
    }


def phase_traces() -> dict[str, list[Path]]:
    """Traces publicados, uma realização técnica por (estado, repetição)."""
    out = {"Hardening (H, R=5)": sorted((ROOT / "docs/evidence/h2/hardening_low_20261004T201555Z/traces").glob("*.jsonl")),
           "B0 (H, R=1)": sorted((ROOT / "docs/evidence/h2/b0_low_20261004T202013Z/traces").glob("*.jsonl"))}
    for name, path, key in (("CAL-A", "docs/evidence/cal_a/run_20261004T231101Z/summary.json", "evaluations"),
                            ("Sequential Dev", "docs/evidence/sequential_dev/run_20261004T235634Z/summary.json",
                             "evaluations"),
                            ("Stress", "docs/evidence/stress/run_20261005T011248Z/summary.json", "trajectories")):
        items = json.loads((ROOT / path).read_text(encoding="utf-8"))[key]
        out[name] = [ROOT / i["runs_root"] / i["run_dir"] / "llm_calls.jsonl" for i in items if i.get("config_id", 1) == 1]
    out["CAL-B v1"] = [RUN / "anchors" / a / "llm_calls.jsonl" for a in CAL_B_ANCHORS]
    return out


def upper_band_reading(paths: list[Path]) -> dict[str, Any]:
    """Afirmações de rompimento da banda superior x sinal real de bb_upper_gap."""
    cells: Counter = Counter()
    for path in paths:
        for r in load_trace(path.read_bytes()):
            if r.request.stage != "technical_analyst" or not r.request.user_prompt.startswith("Features: "):
                continue
            gap = json.loads(r.request.user_prompt.splitlines()[0][len("Features: "):])["bb_upper_gap"]
            claim = bool(re.search(UPPER_BREACH_CLAIM, r.validated_response["justification"], re.IGNORECASE))
            cells[("gap>0" if gap > 0 else "gap<=0", claim, r.validated_response["signal"])] += 1
    def n(side, claim=None, signal=None):
        return sum(v for (g, c, s), v in cells.items() if g == side and (claim is None or c == claim)
                   and (signal is None or s == signal))
    false_claims, inside = n("gap<=0", True), n("gap<=0")
    return {
        "technical_votes": sum(cells.values()),
        "votes_with_price_below_upper_band": inside,
        "false_upper_breach_claims": false_claims,
        "false_claim_rate_when_below_band": round(false_claims / inside, 4) if inside else None,
        "votes_with_price_above_upper_band": n("gap>0"),
        "true_upper_breach_claims": n("gap>0", True),
        "manter_share_when_false_claim": round(n("gap<=0", True, "MANTER") / false_claims, 4) if false_claims else None,
        "manter_share_below_band_without_claim": round(n("gap<=0", False, "MANTER") / (inside - false_claims), 4)
        if inside - false_claims else None,
    }


def prior_phase_decisions() -> dict[str, list[dict[str, Any]]]:
    """Decisões já publicadas, uma realização técnica por (estado, repetição)."""
    def lines(path: Path) -> list[dict]:
        return [json.loads(x) for x in path.read_text(encoding="utf-8").splitlines() if x.strip()]

    phases: dict[str, list[dict]] = {}
    hard = lines(ROOT / "docs/evidence/h2/hardening_low_20261004T201555Z/decisions.jsonl")
    phases["Hardening H_syn (R=5)"] = [x["decision"] for x in hard if x["state_id"].startswith("syn") and x["decision"]]
    phases["Hardening H_real (R=5)"] = [x["decision"] for x in hard if not x["state_id"].startswith("syn") and x["decision"]]
    b0 = lines(ROOT / "docs/evidence/h2/b0_low_20261004T202013Z/decisions.jsonl")
    phases["B0 (H, R=1)"] = [x["decision"] for x in b0 if x["decision"]]
    for name, path, key in (
        ("CAL-A (20 anchors x R=3, config 1)", "docs/evidence/cal_a/run_20261004T231101Z/summary.json", "evaluations"),
        ("Sequential Dev (127 sessions x R=3, D01)", "docs/evidence/sequential_dev/run_20261004T235634Z/summary.json",
         "evaluations"),
        ("Stress (4 windows x R=3)", "docs/evidence/stress/run_20261005T011248Z/summary.json", "trajectories"),
    ):
        items = json.loads((ROOT / path).read_text(encoding="utf-8"))[key]
        items = [i for i in items if i.get("config_id", 1) == 1]  # Technical é igual nas configs pareadas
        phases[name] = [d for i in items for d in lines(ROOT / i["runs_root"] / i["run_dir"] / "decisions.jsonl")
                        if d.get("eligible", True)]
    return phases


def hold_profile(decisions: list[dict[str, Any]]) -> dict[str, Any]:
    causes = Counter(d["final_cause"] for d in decisions)
    votes = Counter()
    for d in decisions:
        votes.update(d["vote_counts"] or {})
    strength = Counter(d["vote_counts"]["MANTER"] for d in decisions if d["final_cause"] == "TECH_EXPLICIT_HOLD")
    total_votes = sum(votes.values())
    return {"decisions": len(decisions),
            "tech_explicit_hold_rate": round(causes["TECH_EXPLICIT_HOLD"] / len(decisions), 4),
            "tech_no_majority_rate": round(causes["TECH_NO_MAJORITY"] / len(decisions), 4),
            "vote_share": {s: round(votes[s] / total_votes, 4) for s in SIGNALS},
            "explicit_hold_strength_5_4_3": [strength[5], strength[4], strength[3]]}


def cell(text: str) -> str:
    return text.replace("|", "\\|").replace("\n", " ")


def markdown(r: dict[str, Any]) -> str:
    """Relatório legível; todo número sai de ``postmortem.json``."""
    A = r["anchors"]
    holds = [a for a in A if a["final_cause"] == "TECH_EXPLICIT_HOLD"]
    ub, dl, cs = r["upper_band_false_claims_cal_b"], r["default_language"], r["consensus"]
    md = [f"# CAL-B v1 — post-mortem do excesso de MANTER", "", f"**{LABEL}**", "",
          "Diagnóstico mecânico, só com artefatos selados (selos conferidos) e decisões/traces já publicados das "
          "fases anteriores. Zero chamadas ao provedor, zero preço/retorno posterior a `t`, zero Validation/Final, "
          "zero mudança de configuração, prompt ou código científico. Nada aqui seleciona parâmetro ou performance.",
          "", "## 1. Tabela por âncora", "",
          "| Anchor | 8 features (canônicas) | Votes C/V/M | Consensus | Mean conf. winner | Final technical | Final cause |",
          "|---|---|---|---|---:|---|---|"]
    for a in A:
        f = ", ".join(f"{k}={v}" for k, v in a["features"].items())
        vc = a["vote_counts"]
        md.append(f"| {a['anchor']} | {f} | {vc['COMPRA']}/{vc['VENDA']}/{vc['MANTER']} | "
                  f"{'yes' if a['consensus_reached'] else 'no'} | {a['mean_confidence_winner']} | "
                  f"{a['technical_outcome']} | {a['final_cause']} |")
    md += ["", "## 2. Cinco votos por âncora (texto original preservado)", ""]
    for a in A:
        md += [f"### {a['anchor']} — {a['technical_outcome']} ({a['final_cause']})", "",
               "| Analyst | Signal | Confidence | Justification | Labels | Upper-band breach claim |", "|---:|---|---:|---|---|---|"]
        for v in a["votes"]:
            claim = "**FALSE** (bb_upper_gap < 0)" if v["upper_band_claim_contradicts_payload"] else (
                "true" if v["upper_band_breach_claim"] else "—")
            md.append(f"| {v['analyst']} | {v['signal']} | {v['confidence']} | {cell(v['justification'])} | "
                      f"{', '.join(v['taxonomy'])} | {claim} |")
        md.append("")
    md += ["## 3. Força do HOLD", "", "| Classe | Âncoras |", "|---|---:|"]
    md += [f"| {k} | {r['hold_strength_distribution'].get(k, 0)} |" for k in ("5/5 HOLD", "4/5 HOLD", "3/5 HOLD")]
    md += ["", "## 4. Minoria não-HOLD nas âncoras MANTER", "", "| Anchor | HOLD | BUY | SELL |", "|---|---:|---:|---:|"]
    md += [f"| {k} | {v['HOLD']} | {v['BUY']} | {v['SELL']} |" for k, v in r["non_hold_minority"].items()]
    md += ["", "## 5. Controle clássico (indicator-family-matched) nas mesmas datas", "",
           "Só barras até close(t); não é avaliação de performance. As famílias são **eventos de cruzamento t-1→t**: "
           "0 significa \"nenhum cruzamento hoje\", não \"estado neutro\".", "",
           "| Anchor | SMA | BB | RSI | MACD | Score | Classical action | LLM technical |", "|---|---:|---:|---:|---:|---:|---|---|"]
    md += [f"| {a['anchor']} | {a['classical_control']['sma']} | {a['classical_control']['bollinger']} | "
           f"{a['classical_control']['rsi']} | {a['classical_control']['macd']} | {a['classical_control']['score']} | "
           f"{a['classical_control']['action']} | {a['technical_outcome']} |" for a in A]
    md += ["", "## 6. Sinais das features (descritivo; sem pesos, sem score)", "",
           "| Anchor | sma50_gap | sma200_gap | Bollinger | %B | RSI | macd_ratio | macd_signal_ratio | macd−signal |",
           "|---|---|---|---|---:|---|---|---|---|"]
    for a in A:
        s = a["feature_signs"]
        md.append(f"| {a['anchor']} | {s['sma50_gap']} | {s['sma200_gap']} | {s['bollinger_position']} | "
                  f"{s['bollinger_percent_b']} | {s['rsi']:.2f} {s['rsi_zone']} | {s['macd_ratio']} | "
                  f"{s['macd_signal_ratio']} | {s['macd_minus_signal']} |")
    fa = r["feature_sign_alignment"]
    md += ["", f"sma50_gap, sma200_gap, macd_ratio e macd−signal com o mesmo sinal: "
               f"{len(fa['sma50_sma200_macd_hist_same_sign'])}/{fa['of']} ({', '.join(fa['sma50_sma200_macd_hist_same_sign'])}).",
           "", "## 7. Leitura da banda superior (achado não previsto na taxonomia)", "",
           "`bb_upper_gap = close/upper − 1` (`src/agents/features.py`): negativo = preço **abaixo** da banda "
           "superior. O prompt técnico transmite só os nomes e valores das 8 razões, sem definição nem convenção de "
           "sinal. Regra textual de afirmação de rompimento/posição acima da banda superior: "
           f"`{r['upper_band_reading_rule']}` (todas as ocorrências da CAL-B conferidas manualmente).", "",
           f"- CAL-B v1: `bb_upper_gap < 0` nas 10 âncoras; afirmações falsas de rompimento em {ub['all_votes'][0]}/"
           f"{ub['all_votes'][1]} votos, {ub['hold_anchor_votes'][0]}/{ub['hold_anchor_votes'][1]} nas âncoras HOLD e "
           f"{ub['manter_votes'][0]}/{ub['manter_votes'][1]} votos MANTER.", "",
           "| Fase | votos técnicos | preço abaixo da banda | afirmações falsas | taxa | preço acima da banda | afirmações verdadeiras | MANTER c/ afirmação falsa | MANTER sem afirmação |",
           "|---|---:|---:|---:|---:|---:|---:|---:|---:|"]
    for k, v in r["upper_band_reading_by_phase"].items():
        md.append(f"| {k} | {v['technical_votes']} | {v['votes_with_price_below_upper_band']} | "
                  f"{v['false_upper_breach_claims']} | {v['false_claim_rate_when_below_band']} | "
                  f"{v['votes_with_price_above_upper_band']} | {v['true_upper_breach_claims']} | "
                  f"{v['manter_share_when_false_claim']} | {v['manter_share_below_band_without_claim']} |")
    md += ["", "## 8. Taxonomia das justificativas (votos das 8 âncoras HOLD, múltiplos rótulos)", "",
           "| Label | Votos |", "|---|---:|"]
    md += [f"| {k} | {v} |" for k, v in sorted(r["taxonomy_counts_hold_anchor_votes"].items(), key=lambda x: -x[1])]
    md += ["", "Regras: " + "; ".join(f"`{k}` = `{v}`" for k, v in r["taxonomy_rules"].items()), "",
           "## 9. MANTER como default de segurança", "",
           f"- linguagem de segurança/incerteza (`{'|'.join(r['default_language_rules'])}`): "
           f"{dl['manter_votes_with_safety_default_language'][0]}/{dl['manter_votes_with_safety_default_language'][1]} "
           f"votos MANTER vs {dl['directional_votes_with_safety_default_language'][0]}/"
           f"{dl['directional_votes_with_safety_default_language'][1]} votos direcionais;",
           f"- visão neutra declarada (`{'|'.join(r['neutral_view_rules'])}`): "
           f"{dl['manter_votes_with_neutral_view_language'][0]}/{dl['manter_votes_with_neutral_view_language'][1]} "
           f"votos MANTER; nenhuma das duas: {dl['manter_votes_with_neither'][0]}/{dl['manter_votes_with_neither'][1]};",
           f"- confidence de MANTER exatamente 0.65 em {dl['manter_confidence_exactly_0_65'][0]}/"
           f"{dl['manter_confidence_exactly_0_65'][1]} votos.", "", "Trechos literais:", ""]
    md += [f"- {a['anchor']} #{v['analyst']}: “…{v['default_language'][0]}…”" for a in A for v in a["votes"]
           if v["default_language"]]
    md += ["", "## 10. Confidence por sinal (descritivo; não entra em sizing nem seleção)", "",
           "| Signal | n | média | mediana | min | max |", "|---|---:|---:|---:|---:|---:|"]
    md += [f"| {k} | {v['n']} | {v.get('mean')} | {v.get('median')} | {v.get('min')} | {v.get('max')} |"
           for k, v in r["confidence_by_signal"].items()]
    md += ["", "## 11. Consenso e N contrafactual (só os 5 votos existentes)", "",
           f"- `TECH_NO_MAJORITY` = {cs['tech_no_majority']}; menor número de votos do vencedor = {cs['min_winner_votes']}/5; "
           f"reduzir o limiar de 3/5 mudaria alguma decisão: {'sim' if cs['lower_threshold_changes_any_decision'] else 'não'}.",
           "", "| Anchor | Votes C/V/M | primeiros 3 | primeiros 4 | todos 5 |", "|---|---|---|---|---|"]
    for a in A:
        vc, cf = a["vote_counts"], a["counterfactual_prefix_majority"]
        md.append(f"| {a['anchor']} | {vc['COMPRA']}/{vc['VENDA']}/{vc['MANTER']} | {cf['first_3']} | {cf['first_4']} | {cf['first_5']} |")
    rc = r["risk_contribution"]
    md += ["", "## 12. Contribuição de Risk/Portfolio", "",
           f"- TECHNICAL INACTIVITY: {len(rc['technical_inactivity'])} âncoras ({', '.join(rc['technical_inactivity'])}): "
           "consenso MANTER, Risk AUTO_APPROVE, Portfolio não chamado.",
           f"- RISK SUPPRESSION: {len(rc['risk_suppression'])} ({', '.join(rc['risk_suppression'])}): COMPRA 5/5 vetada pela "
           "regra dura de volatilidade antes do LLM de risco.",
           f"- HOLDs com chamada de Risk/Portfolio LLM: {len(rc['holds_with_risk_or_portfolio_llm_call'])}.", "",
           "## 13. Taxa de HOLD por fase (sem performance)", "",
           "| Fase | decisões | TECH_EXPLICIT_HOLD | NO_MAJORITY | votos MANTER | votos COMPRA | votos VENDA | HOLD 5/5, 4/5, 3/5 |",
           "|---|---:|---:|---:|---:|---:|---:|---|"]
    for k, v in r["prior_phases"].items():
        md.append(f"| {k} | {v['decisions']} | {v['tech_explicit_hold_rate']} | {v['tech_no_majority_rate']} | "
                  f"{v['vote_share']['MANTER']} | {v['vote_share']['COMPRA']} | {v['vote_share']['VENDA']} | "
                  f"{v['explicit_hold_strength_5_4_3']} |")
    md += ["", DIAGNOSIS.strip(), ""]
    return "\n".join(md)


#: Leitura dos autores-assistentes sobre os números acima (texto fixo; números
#: conferidos contra ``postmortem.json``).
DIAGNOSIS = """
## 14. Diagnóstico

**PRIMARY_DIAGNOSIS = E — MIXED**, com um mecanismo dominante identificado:
um defeito de **semântica de feature** no contrato do prompt técnico, que se
soma a neutralidade real de parte dos estados e a linguagem de cautela. C e D
estão descartados.

Componentes, em ordem de peso da evidência:

1. **Leitura errada de `bb_upper_gap` (contrato do prompt sub-especificado).**
   Nas 10 âncoras o preço está abaixo da banda superior, mas 27 dos 40 votos
   das âncoras HOLD (24/36 votos MANTER) afirmam que o preço "rompeu/ultrapassou
   a banda superior" e usam essa sobrecompra inexistente como contra-argumento
   à tendência de alta. O erro não é da CAL-B: ocorre em 33–43% dos votos com o
   preço abaixo da banda em todas as fases anteriores, e quase nunca há
   afirmação correta quando o preço está de fato acima da banda. O prompt
   transmite os nomes das 8 razões sem definição nem convenção de sinal. Das
   3 âncoras HOLD em que SMA50, SMA200, MACD e MACD − sinal têm o mesmo sinal
   (2019-10-15, 2021-08-20, 2022-03-31), em duas (2019-10-15 e 2022-03-31)
   todos os 5 votos citam o rompimento falso; a terceira (2021-08-20,
   sma50_gap 0.0027, RSI 51.6) justifica MANTER por neutralidade.
2. **Neutralidade/conflito real em parte dos estados (B parcial).** RSI entre
   51.6 e 64.9 nas 8 âncoras HOLD; em 5 das 8, o sinal da tendência (SMA) e o
   do momentum (MACD − sinal) discordam (2018-07-19, 2019-03-07, 2020-06-01,
   2021-01-13, 2024-01-22). 2021-08-20 e 2024-01-22 não citam o rompimento
   falso e justificam MANTER por neutralidade/consolidação. O controle clássico
   não ajuda a separar: é de eventos de cruzamento e dá 0 em 6 das 8 âncoras
   HOLD.
3. **MANTER como default de cautela (A parcial).** 9/36 votos MANTER usam
   linguagem de cautela/confirmação (0/14 votos direcionais); 32/36 têm
   confidence exatamente 0.65. A maioria (25/36) declara visão neutra, então a
   evidência de fallback de segurança existe, mas não é o mecanismo principal.

Descartados: **C — ensemble**: 5 das 8 âncoras HOLD são 5/5 e 2 são 4/5; 72%
dos votos individuais são MANTER; nenhum NO_MAJORITY; baixar o limiar não muda
nada; só 2022-03-31 mudaria com os 3 primeiros votos (COMPRA). **D —
Risk/Portfolio**: nenhum dos 8 HOLDs passou por Risk ou Portfolio LLM; a única
supressão de risco (2022-11-04) é o veto duro de volatilidade de uma COMPRA 5/5.

**Salto ou continuação?** Continuação. A taxa de TECH_EXPLICIT_HOLD da CAL-B
(0.80) fica no alto da faixa das fases anteriores (0.47–0.75; H_real 0.75,
Sequential Dev 0.63), e a parcela de votos MANTER (0.72) é próxima da do H_real
(0.78). Ilustração (supõe independência): com a taxa do Sequential Dev, 8+
holds em 10 âncoras teriam probabilidade ≈ 0.22. O gate do Hardening passou
com total_hold_rate 0.633 calculado sobre H, que mistura H_syn (explicit hold
0.55) e H_real (0.75).

## 15. O que esta evidência sustenta

- O excesso de MANTER é **do Technical**, não de Risk/Portfolio nem da
  agregação.
- O Technical v1 lê sistematicamente errado a convenção de sinal de
  `bb_upper_gap`, desde o Hardening, e usa a leitura errada como argumento
  contra entrar.
- Parte dos estados da CAL-B tem conflito real entre tendência e momentum, com
  RSI neutro.
- A CAL-B não foi um salto; a propensão a MANTER já existia em development, e
  o gate do Hardening (sobre H com estados sintéticos) não a capturou.

## 16. O que esta evidência NÃO sustenta

- Que o sistema "deveria" ter negociado nessas datas, ou que mais negociação
  seria melhor: nenhum retorno foi olhado.
- Que corrigir a semântica das features reduziria os HOLDs abaixo de 0.90, ou
  quanto: não houve nova inferência.
- Causalidade entre a leitura errada e o MANTER: a associação é descritiva e
  muda de sentido entre fases (em Hardening, B0 e CAL-B os votos com a
  afirmação falsa são mais vezes MANTER; em CAL-A, Sequential Dev e Stress,
  menos).
- Qualquer escolha de prompt, temperature, thinking, N ou limiar.
- As taxonomias por regra textual são aproximações; o texto original está
  preservado acima para conferência.

## 17. Classe mínima de defeito recomendada

**TECHNICAL PROMPT CONTRACT — FEATURE SEMANTICS UNDER-SPECIFIED.** O prompt
técnico entrega 8 razões adimensionais sem definição nem convenção de sinal, e
o modelo interpreta pelo menos uma delas (`bb_upper_gap`) ao contrário de forma
sistemática. É defeito objetivo, detectável sem resultado financeiro (a
afirmação contradiz o dado fornecido), e a classe de correção mínima é
documentar no contrato o significado e o sinal de cada feature. O objetivo
dessa correção é leitura correta do dado, não aumentar a taxa de negociação.
"Conservadorismo do prompt" fica como fator secundário a reavaliar depois da
correção, não como alvo de tuning. O texto exato não é proposto aqui.
"""


def main() -> None:
    verify_seal(RUN)  # artefatos exatamente como selados
    packet = json.loads((RUN / "audit_packet.json").read_text(encoding="utf-8"))
    _, frame = load_frame()
    control = IndicatorFamilyControlParticipant("PETR4.SA")
    anchors, all_votes = [], []
    for e in packet:
        anchor = e["anchor"]
        decision = json.loads((RUN / "anchors" / anchor / "decisions.jsonl").read_text(encoding="utf-8").splitlines()[0])
        tech = sorted((c for c in e["calls"] if c["stage"] == "technical_analyst"), key=lambda c: c["analyst_id"])
        votes = [{"analyst": c["analyst_id"], **c["visible_output"]} for c in tech]
        for v in votes:
            v["taxonomy"] = labels(v["justification"])
            v["default_language"] = snippets(v["justification"], DEFAULT_LANGUAGE)
            v["neutral_view_language"] = snippets(v["justification"], NEUTRAL_VIEW)
            m = re.search(UPPER_BREACH_CLAIM, v["justification"], re.IGNORECASE)
            v["upper_band_breach_claim"] = m.group(0) if m else None
            v["upper_band_claim_contradicts_payload"] = bool(m) and e["technical_feature_payload"]["bb_upper_gap"] <= 0
            all_votes.append({"anchor": anchor, **v})
        signals = [v["signal"] for v in votes]
        outcome = decision["technical_outcome"]
        winners = [v["confidence"] for v in votes if v["signal"] == outcome]
        family = control.family_signals(history_until(frame, anchor)["fechamento"])  # só até close(t)
        score = sum(family.values())
        anchors.append({
            "anchor": anchor,
            "features": e["technical_feature_payload"],
            "feature_signs": feature_signs(e["technical_feature_payload"]),
            "vote_counts": decision["vote_counts"],
            "consensus_reached": decision["consensus_reached"],
            "technical_outcome": outcome,
            "mean_confidence_winner": round(statistics.fmean(winners), 4) if winners else None,
            "final_cause": decision["final_cause"],
            "reason_codes": e["reason_codes"],
            "votes": votes,
            "hold_strength": f"{decision['vote_counts']['MANTER']}/5 HOLD" if decision["final_cause"] ==
            "TECH_EXPLICIT_HOLD" else None,
            "counterfactual_prefix_majority": {f"first_{n}": majority(signals[:n]) for n in (3, 4, 5)},
            "classical_control": {**family, "score": score,
                                  "action": "COMPRA" if score > 0 else "VENDA" if score < 0 else "MANTER"},
        })

    holds = [a for a in anchors if a["final_cause"] == "TECH_EXPLICIT_HOLD"]
    hold_votes = [v for v in all_votes if any(a["anchor"] == v["anchor"] for a in holds)]
    manter_votes = [v for v in all_votes if v["signal"] == "MANTER"]
    directional = [v for v in all_votes if v["signal"] != "MANTER"]
    with_default = lambda vs: sum(bool(v["default_language"]) for v in vs)  # noqa: E731
    sign_aligned = [a["anchor"] for a in anchors if len({a["feature_signs"][k] for k in
                    ("sma50_gap", "sma200_gap", "macd_ratio", "macd_minus_signal")}) == 1]
    report = {
        "label": LABEL,
        "kind": "CAL_B_V1_POSTMORTEM",
        "inputs": "sealed CAL-B v1 artifacts (seals verified) + published prior-phase decisions; "
                  "classical control on bars up to close(t) only",
        "safety": {"provider_calls": 0, "t_plus_1_prices_or_returns": 0, "validation": 0, "final_test": 0,
                   "configuration_changes": 0},
        "anchors": anchors,
        "hold_strength_distribution": dict(Counter(a["hold_strength"] for a in holds)),
        "non_hold_minority": {a["anchor"]: {"HOLD": a["vote_counts"]["MANTER"], "BUY": a["vote_counts"]["COMPRA"],
                                            "SELL": a["vote_counts"]["VENDA"]} for a in holds},
        "taxonomy_counts_hold_anchor_votes": dict(Counter(l for v in hold_votes for l in v["taxonomy"])),
        "taxonomy_rules": {**TAXONOMY, "TREND_MOMENTUM_CONFLICT": f"({TREND}) & ({MOMENTUM}) & ({CONTRAST})"},
        "default_language_rules": list(DEFAULT_LANGUAGE),
        "neutral_view_rules": list(NEUTRAL_VIEW),
        "default_language": {
            "manter_votes_with_safety_default_language": [with_default(manter_votes), len(manter_votes)],
            "directional_votes_with_safety_default_language": [with_default(directional), len(directional)],
            "manter_votes_with_neutral_view_language": [sum(bool(v["neutral_view_language"]) for v in manter_votes),
                                                        len(manter_votes)],
            "manter_votes_with_neither": [sum(not v["default_language"] and not v["neutral_view_language"]
                                              for v in manter_votes), len(manter_votes)],
            "manter_confidence_exactly_0_65": [sum(v["confidence"] == 0.65 for v in manter_votes), len(manter_votes)],
        },
        "confidence_by_signal": {s: stats([v["confidence"] for v in all_votes if v["signal"] == s]) for s in SIGNALS},
        "consensus": {
            "tech_no_majority": sum(a["final_cause"] == "TECH_NO_MAJORITY" for a in anchors),
            "min_winner_votes": min(max(a["vote_counts"].values()) for a in anchors),
            "lower_threshold_changes_any_decision": any(max(a["vote_counts"].values()) < 3 for a in anchors),
            "prefix_changes_direction": {f"first_{n}": [a["anchor"] for a in anchors
                                                       if a["counterfactual_prefix_majority"][f"first_{n}"]
                                                       != a["technical_outcome"]] for n in (3, 4)},
        },
        "risk_contribution": {
            "technical_inactivity": [a["anchor"] for a in holds],
            "risk_suppression": [a["anchor"] for a in anchors if a["final_cause"].startswith("RISK_VETO")],
            "holds_with_risk_or_portfolio_llm_call": [a["anchor"] for a in holds
                                                       if a["reason_codes"]["risk_source"] != "AUTO_APPROVE"
                                                       or a["reason_codes"]["portfolio_called"]],
        },
        "feature_sign_alignment": {"sma50_sma200_macd_hist_same_sign": sign_aligned, "of": len(anchors)},
        "upper_band_reading_rule": UPPER_BREACH_CLAIM,
        "upper_band_reading_by_phase": {name: upper_band_reading(paths) for name, paths in phase_traces().items()},
        "upper_band_false_claims_cal_b": {
            "all_votes": [sum(v["upper_band_claim_contradicts_payload"] for v in all_votes), len(all_votes)],
            "hold_anchor_votes": [sum(v["upper_band_claim_contradicts_payload"] for v in hold_votes), len(hold_votes)],
            "manter_votes": [sum(v["upper_band_claim_contradicts_payload"] for v in manter_votes), len(manter_votes)],
        },
        "classical_control_actions": dict(Counter(a["classical_control"]["action"] for a in anchors)),
        "prior_phases": {**{name: hold_profile(ds) for name, ds in prior_phase_decisions().items()},
                         "CAL-B v1 (10 anchors x R=1)": hold_profile(
                             [json.loads((RUN / "anchors" / a / "decisions.jsonl").read_text(encoding="utf-8")
                                         .splitlines()[0]) for a in CAL_B_ANCHORS])},
    }
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "postmortem.json").write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n",
                                         encoding="utf-8", newline="\n")
    (OUT / "POSTMORTEM.md").write_text(markdown(report), encoding="utf-8", newline="\n")
    print(json.dumps({k: report[k] for k in ("hold_strength_distribution", "taxonomy_counts_hold_anchor_votes",
                                             "default_language", "confidence_by_signal", "consensus",
                                             "risk_contribution", "feature_sign_alignment",
                                             "upper_band_false_claims_cal_b", "upper_band_reading_by_phase",
                                             "classical_control_actions", "prior_phases")}, indent=1,
                     ensure_ascii=False))


if __name__ == "__main__":
    main()
