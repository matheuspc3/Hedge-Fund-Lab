"""Read-only readiness diagnostic: stdout only, no downloads, inference or writes.

Default output is a sectioned summary; ``--json`` prints the full overview.
Exit code 2 when H2 integrity cannot be verified.
"""

import argparse
import json
import sys
from pathlib import Path

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "dashboard"), str(ROOT / "scripts"), str(ROOT)]
import platform_api  # noqa: E402

from src.experiments.h2_evaluation_offline import no_network  # noqa: E402

UNAVAILABLE = "INDISPONÍVEL (registro ausente ou integridade divergente)"


def radar_rows(i):
    """One ticker: state, input identity/provenance, normalization, risk, preflight."""
    rows = [
        f"{i['ticker']}: {i['state']} · input {i['input_state']} · parecer {i['opinion']}"
    ]
    facts = i.get("input")
    if facts:
        norm = facts["normalization"]
        events = ", ".join(
            f"{e['type']} {e['ex_date']} x{e['yfinance_split_ratio']} ({e['b3_especi']})"
            for e in norm["events"]
        )
        risk = facts["risk"]
        rows += [
            f"    sessão {i['session']} · {facts['bars']} barras desde {facts['history_start']}"
            f" · input {facts['input_sha256'][:16]}… · barras {facts['bars_sha256'][:16]}…",
            f"    fonte {facts['source']} · fechamento bruto {facts['raw_close']}"
            f" · ajustado {facts['adjusted_close']}",
            f"    normalização {norm['state']} ({norm['extractor']}){': ' + events if events else ''}",
            f"    risco individual: vol21 {risk['asset_volatility_21']} / limite {risk['limit']}"
            + (" · RESTRIÇÃO: veto determinístico esperado" if risk["restricted"] else "")
            + (
                f" · veredito {i['risk_verdict']}"
                if i["risk_verdict"]
                else " · sem parecer de risco"
            ),
        ]
    rows.append(f"    preflight {i['preflight']} · {i['action']}")
    if i.get("error"):
        rows.append(f"    erro registrado: {i['error']}")
    return rows


def run_rows(r):
    """One registered Radar run: identity, records, money, integrity, Global PM use."""
    money = r["budget"]
    rows = [
        f"{r['id']}: {r['state']}"
        + (f" ({', '.join(r['reasons'])})" if r["reasons"] else "")
        + (" · SELECIONADA" if r["selected"] else "")
        + (f" · INCIDENTE {r['incident']['id']}" if r["incident"] else ""),
        f"    raiz {r['path']} · sessão {r['session']} · fonte {r['source']} ({r['classification']})"
        f" · universo {' '.join(r['universe'])}",
        f"    tratamento {r['treatment']['identity']} manifesto {r['treatment']['manifest_sha256'][:16]}…"
        + (
            f" · nova instância do mesmo tratamento de {r['same_treatment_as']}"
            if r["same_treatment_as"]
            else ""
        ),
        f"    inputs {r['inputs']}/{len(r['universe'])} · pareceres {r['opinions']} · claims {r['claims']}"
        f" · falhas {r['failures']} · chamadas reservadas {r['calls_reserved']}"
        f" · respostas gravadas {r['responses_recorded']}",
        f"    integridade {r['integrity']}{': ' + ', '.join(r['errors']) if r['errors'] else ''}"
        f" · aceita novas chamadas: {'sim' if r['accepts_new_calls'] else 'NÃO'}"
        f" · disponível ao Global PM: {'sim' if r['global_pm_available'] else 'não'}"
        + (
            f" · análises fora da identidade: {', '.join(r['outside_identity'])}"
            if r["outside_identity"]
            else ""
        ),
    ]
    if money:
        rows += [
            f"    orçamento próprio US$ {r['budget_usd']} · reservado US$ {r['usd_reserved']}"
            f" (resultado incerto US$ {r['usd_reserved_uncertain']}) · custo observado pelos tokens"
            f" US$ {r['usd_observed_provider_tokens']} · faturado confirmado: DESCONHECIDO",
            f"    próximo lote: {money['planned']['calls_planned']} chamadas planejadas"
            f" (máx. {money['planned']['calls_max']}) · reserva US$ {money['planned']['usd_reserved']}"
            f" · exposição agregada US$ {money['aggregate_exposure_usd']} / limite local"
            f" US$ {money['aggregate_cap_usd']} · autorização de orçamento {money['authorization']['state']}",
        ]
        rows += [
            f"    reserva {b['batch']}…: US$ {b['usd_reserved']} · {b['outcome']} · {b['forensic']}"
            for b in next(x for x in money["runs"] if x["run"] == r["id"])["reservations"]
        ]
    if r["comparison"]:
        c = r["comparison"]
        rows.append(
            f"    comparação econômica com {c['reference']}: "
            + ("DIVERGÊNCIA MATERIAL" if c["material"] else "sem divergência material")
            + " · "
            + ", ".join(f"{i['ticker']} {i['status']}" for i in c["items"])
        )
    return rows


def summary(d):
    """Sections requested for the operator; every line comes from ``overview``."""
    data = lambda key: d[key]["data"] if d[key]["available"] else None  # noqa: E731
    lines = [f"HFL · diagnóstico somente leitura · {d['observed_at']}"]

    def section(title, rows):
        lines.append("")
        lines.append(f"[{title}]")
        lines.extend("  " + row for row in rows)

    decision = data("decision")
    section(
        "H2 original",
        [
            f"decisão {decision['status']} · sessão {decision['session']} · "
            f"alvo {decision.get('target_session')} · gerada {decision.get('generated_at')}",
            f"ordem: {(decision.get('order') or {}).get('detail', 'N/D')}",
            "decisão existente: não repetir a inferência desta sessão.",
        ]
        if decision
        else [
            "nenhuma decisão disponível" if d["decision"]["available"] else UNAVAILABLE
        ],
    )
    sup = (data("supervision") or {}).get("selected")
    audit = (data("supervision") or {}).get("audit") or {}
    section(
        "Supervisão",
        [
            f"estado {sup['order_state']} · prazo {sup.get('deadline')} · "
            f"aprovação {'registrada' if sup.get('approval') else 'nenhuma'}",
            f"auditoria {'íntegra' if audit.get('ok') else 'NÃO VERIFICADA'} · "
            f"{audit.get('events', 'N/D')} eventos",
        ]
        if sup
        else [
            "sem proposta selecionada" if d["supervision"]["available"] else UNAVAILABLE
        ],
    )
    wallets = (data("wallets") or {}).get("wallets", [])
    section(
        "Carteiras e benchmarks",
        [
            f"{w['label']}: patrimônio {w.get('equity')} · caixa {w.get('cash')} · "
            f"posições {', '.join(f'{p['asset']} {p['units']}' for p in w.get('composition', []) if p.get('units')) or 'nenhuma'} · "
            f"marca {(w.get('mark') or {}).get('session')} · "
            f"ordem {('para ' + w['pending']['target_session']) if w.get('pending') else 'nenhuma'}"
            + ("" if w.get("comparable") is not False else " · NÃO COMPARÁVEL")
            if w.get("available")
            else f"{w.get('label', w.get('key'))}: indisponível"
            for w in wallets
        ]
        or [UNAVAILABLE],
    )
    readiness = data("official_selection")
    section(
        f"Radar oficial · execução {d.get('radar_run_selected') or 'legada'} · sessão "
        f"{(readiness or {}).get('session', d['last_closed_session'])}",
        [
            readiness["summary"]
            + f" · preflight do lote {'pronto' if readiness['radar_preflight']['ready'] else 'bloqueado'}",
            "preparo (equivale ao botão de /radar; grava, sem Gemini): "
            + readiness["prepare_command"],
        ]
        + [row for i in readiness["items"] for row in radar_rows(i)]
        + [
            "pendências para Gemini: "
            + (", ".join(readiness["gemini_pending"]) or "nenhuma além da autorização")
        ]
        if readiness
        else [UNAVAILABLE],
    )
    runs = data("radar_runs")
    section(
        "Execuções Radar (registry = índice; autoridade = registros de cada raiz)",
        [
            f"registry revisão {runs['revision']} · selecionada {runs['selected']}"
            f" · {len(runs['runs'])} execução(ões)"
        ]
        + [row for r in runs["runs"] for row in run_rows(r)]
        if runs
        else [UNAVAILABLE + " · nenhuma execução é selecionada automaticamente"],
    )
    records = d["global_records"]
    section(
        "Global PM",
        [
            (
                f"elegibilidade oficial: {'PRONTA' if readiness['global_pm_ready'] else 'BLOQUEADA'}"
                f" · {readiness['summary']}"
                + (
                    f" · faltam {', '.join(readiness['missing'])}"
                    if readiness["missing"]
                    else ""
                )
                if readiness
                else "elegibilidade oficial: N/D"
            )
            + " · contexto oficial só deve ser preparado perto do uso (validade 24 h);"
            " autorização Radar não vale para o Global PM."
        ]
        + [
            f"{r['id']} · {r.get('mode')} · {r['native_state']} · expira {r.get('expires_at')}"
            for r in records
        ],
    )
    cal = d["calendar"]
    section(
        "Mercado",
        [
            f"última sessão observada {d['last_observed_session']} · último fechamento "
            f"do calendário {d['last_closed_session']} · coleta {d['last_input_observed_at']}",
            f"próxima sessão {cal.get('next_session')} · abertura prevista "
            f"{cal.get('expected_open')} (previsão de calendário, não confirma leilão)",
            "cotação intradiária indisponível nesta consulta.",
        ],
    )
    jobs = [
        j
        for j in (data("jobs") or [])
        if j["state"] in ("RUNNING", "FAILED", "RECOVERY_REQUIRED", "BLOCKED")
    ]
    section(
        "Jobs incompletos, incertos ou bloqueados",
        [
            f"{j['module']} · {j.get('command')} · {j['native_state']} → {j['state']}"
            for j in jobs
        ]
        or (["nenhum"] if d["jobs"]["available"] else [UNAVAILABLE]),
    )
    integrity = data("integrity") or {}
    section(
        "Integridade",
        [
            f"H2: {'íntegra' if integrity.get('ok') else 'NÃO VERIFICADA'} · "
            f"{integrity.get('decisions', 'N/D')} decisão(ões) · manifesto {integrity.get('manifest_sha256')}",
            f"V5 demo: {'íntegra' if ((data('synthetic_v5') or {}).get('integrity') or {}).get('ok') else 'indisponível'}",
        ],
    )
    attention = d["attention"]
    section(
        "Ações manuais pendentes",
        [f"PRÓXIMA: {attention['next_action']}"]
        + [f"{i['level']}: {i['text']}" for i in attention["items"][1:]],
    )
    lines.append("")
    lines.append(
        "Nada foi baixado, gravado, aprovado, inferido ou reconciliado por este diagnóstico."
    )
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="full overview JSON")
    args = parser.parse_args()
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    # Same Radar runner the server would bind (module global only; nothing is written).
    platform_api.runs.bind(platform_api.radar_api)
    with no_network():
        report = platform_api.overview()
    print(
        json.dumps(report, ensure_ascii=False, indent=2, default=str)
        if args.json
        else summary(report)
    )
    if not report["integrity"]["available"] or not (
        report["integrity"].get("data") or {}
    ).get("ok"):
        raise SystemExit(2)


if __name__ == "__main__":
    main()
