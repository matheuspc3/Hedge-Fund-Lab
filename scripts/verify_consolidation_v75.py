"""V7.5 scientific consolidation: evidence manifest and metrics, recomputed offline.

Reads only: no provider, no network, no project imports, nothing written under data/.
Needs the local (git-ignored) Radar recovery and Global PM V1/V2 records.

Usage (project root):
  python -B scripts/verify_consolidation_v75.py          # CONSULTA: exit 1 on any divergence
  python -B scripts/verify_consolidation_v75.py build    # GRAVA METRICS.json e EVIDENCE_MANIFEST.json
"""

import argparse
import glob
import hashlib
import json
import sys
from decimal import ROUND_HALF_EVEN, Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = "docs/evidence/hfl_scientific_consolidation_v75"
RADAR = "data/radar/hfl_multiasset_v1_recovery_01"
DAY = "2026-10-09"
V1 = "data/global_pm/hfl_global_pm_v1/v7-5a78ea5d15214e37bcae18f167ffcee3"
V2 = "data/global_pm/hfl_global_pm_v2/v74-76d07c0d32444cecaf07e875deacb519"
TICKERS = ("PETR4", "VALE3", "ITUB4", "WEGE3", "BBAS3")
RESERVATION = f"{RADAR}/reservations/1308e28defa4fa1baf0942b780d35123d675005e01f59fb60f862868d97447ae.json"
RECORD = (
    "context.json",
    "authorization.json",
    "claim.json",
    "private/provider_journal.jsonl",
    "private/calls.sqlite",
    "result.json",
)
#: Lexical proxy over free text only; presence of a term is not a semantic verdict.
TERMS = ("setor", "regulament", "correção imediata", "rompimento")
CLASSES = {
    "PRIMARY": "Resultado bruto ou selado produzido pela execução (ou código cujo hash está selado nela).",
    "DERIVED": "Calculado deterministicamente a partir das evidências primárias.",
    "DIAGNOSTIC": "Reprodução, contrafactual, forense ou snapshot de preservação posterior.",
    "INTERPRETATIVE": "Análise humana ou síntese que não corresponde diretamente a um campo observado.",
    "SYNTHETIC": "Construído com dados ou planner falsos para testes; nunca resultado do Gemini.",
}

#: Which metrics and sources support each table or conclusion of the package.
PROVENANCE = {
    "Resultados do Radar (relatório §6, matriz de agentes)": {
        "metrics": [
            "radar.opinions_completed",
            "radar.valid_analyst_votes",
            "radar.provider_calls",
            "radar.risk_vetoes",
            "radar.per_asset",
            "radar.result_pins_match",
        ],
        "sources": [
            f"{RADAR}/analyses/*/{DAY}/result.json",
            f"{RADAR}/analyses/*/{DAY}/provider_journal.jsonl",
        ],
    },
    "Incidente do lote Radar original (relatório §5)": {
        "metrics": ["radar.original_incident"],
        "sources": [
            "docs/evidence/hfl_incident_2026_10_12/forensics.json",
            "docs/evidence/hfl_radar_v73/compare_recovery_vs_original.json",
        ],
    },
    "Comparação V1 x V2 (COMPARISON_V1_V2.md)": {
        "metrics": [
            "gpm_v1.identity",
            "gpm_v2.identity",
            "gpm_v1.outcome",
            "gpm_v2.outcome",
            "gpm_v1.integrity",
            "gpm_v2.integrity",
            "gpm_v1.usage",
            "gpm_v2.usage",
            "gpm.same_opinions_v1_v2",
        ],
        "sources": [
            f"{V1}/result.json",
            f"{V1}/context.json",
            f"{V2}/result.json",
            f"{V2}/context.json",
        ],
    },
    "Estudo de caso da rejeição V1 (relatório §7)": {
        "metrics": [
            "gpm_v1.outcome",
            "gpm_v1.free_text_terms",
            "gpm_v1.itub4_close_inside_upper_band",
        ],
        "sources": [
            f"{V1}/result.json",
            "docs/evidence/hfl_global_pm_v2/incident_reproduction.json",
            "docs/evidence/hfl_global_pm_v2/README.md",
        ],
    },
    "Análise da resposta V2 (relatório §8)": {
        "metrics": [
            "gpm_v2.outcome",
            "gpm_v2.integrity",
            "gpm_v2.cited_metrics",
            "gpm_v2.watchlist_signals_match",
            "gpm_v2.free_text_terms",
        ],
        "sources": [
            f"{V2}/result.json",
            f"{V2}/context.json",
            "scripts/multiasset_global_pm_v2.py",
        ],
    },
    "Linha do tempo (relatório §5)": {
        "metrics": [
            "radar.batch_window",
            "radar.original_incident",
            "gpm_v1.timeline",
            "gpm_v2.timeline",
        ],
        "sources": [
            f"{RADAR}/analyses/*/{DAY}/claim.json",
            f"{V1}/claim.json",
            f"{V2}/claim.json",
        ],
    },
    "Custos e tokens (COST_ACCOUNTING.md)": {
        "metrics": [
            "radar.tokens",
            "radar.usd_observed_lower_bound",
            "radar.sealed_cost_usd_sum",
            "radar.usd_reserved",
            "radar.usd_planning_estimate",
            "gpm_v1.usage",
            "gpm_v2.usage",
            "gpm.token_delta_v2_minus_v1",
        ],
        "sources": [RESERVATION, f"{V1}/authorization.json", f"{V2}/authorization.json"],
    },
    "Contagem de inferências e desfechos (METRICS, TCC)": {
        "metrics": ["gpm.records_by_planner", "gpm.real_outcomes"],
        "sources": ["data/global_pm/*/*/result.json"],
    },
    "Contrafactual V1 (somente diagnóstico)": {
        "metrics": [],
        "sources": [
            "docs/evidence/hfl_global_pm_v2/incident_reproduction.json",
            "scripts/run_global_pm_v2.py",
        ],
    },
}
#: Numbers transcribed into Markdown tables; check() confirms each still appears there.
DOC_FACTS = {
    "COMPARISON_V1_V2.md": ("gpm_v1.usage", "gpm_v2.usage"),
    "COST_ACCOUNTING.md": ("gpm_v1.usage", "gpm_v2.usage", "radar.tokens"),
}


def sha(path):
    return hashlib.sha256((ROOT / path).read_bytes()).hexdigest()


def load(path):
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def journal(path):
    text = (ROOT / path).read_text(encoding="utf-8")
    return [json.loads(line)["record"] for line in text.splitlines() if line.strip()]


def src(path, cls, nature, relation, treatment=None, immutability="IMMUTABLE"):
    return {
        "path": path,
        "classification": cls,
        "nature": nature,
        "treatment": treatment,
        "immutability": immutability,
        "versioned_in_git": not path.startswith("data/"),
        "relation": relation,
    }


def sources():
    radar_t = "HFL-MULTIASSET-RADAR-V1"
    s = []
    for t in TICKERS:
        base = f"{RADAR}/analyses/{t}/{DAY}/"
        rel = f"comitê {t} da execução radar-2026-10-09-recovery-01"
        s += [
            src(base + "bars.csv", "PRIMARY", "série de preços congelada", rel, radar_t),
            src(
                base + "input.json", "PRIMARY", "input congelado (features)", rel, radar_t
            ),
            src(base + "claim.json", "PRIMARY", "claim do lote pago", rel, radar_t),
            src(
                base + "provider_journal.jsonl",
                "PRIMARY",
                "journal do provedor",
                rel,
                radar_t,
            ),
            src(base + "calls.sqlite", "PRIMARY", "banco de chamadas", rel, radar_t),
            src(base + "result.json", "PRIMARY", "parecer oficial selado", rel, radar_t),
        ]
    s += [
        src(
            RESERVATION,
            "PRIMARY",
            "reserva do lote Radar",
            "orçamento do lote recovery-01",
            radar_t,
        ),
        src(
            f"{RADAR}/budget_authorizations/0fcb1d9b787045b702ede4ec2560416814ca323815f5ed11920a5adb5f9fc2c8.json",
            "PRIMARY",
            "autorização humana de orçamento",
            "orçamento do lote recovery-01",
            radar_t,
        ),
        src(
            "data/radar/registry.json",
            "PRIMARY",
            "índice de execuções Radar",
            "identifica recovery-01 como instância do tratamento original",
            radar_t,
            "OPERATIONAL",
        ),
    ]
    for root, ident, reservation in (
        (
            V1,
            "HFL-MULTIASSET-GLOBAL-PM-V1",
            "data/global_pm/hfl_global_pm_v1/reservations/bdb948aff7ceaf8b473e8132872695ac2d17c1f8cc19daeeabba6ca86baf51a5.json",
        ),
        (
            V2,
            "HFL-MULTIASSET-GLOBAL-PM-V2",
            "data/global_pm/hfl_global_pm_v2/reservations/13ad05f324c6a66f600d9391a1a2658af9f7d18780b6055987a216529728b938.json",
        ),
    ):
        rel = f"registro {root.rsplit('/', 1)[1]}; pareceres = 5 result.json do Radar recovery-01"
        s += [
            src(f"{root}/{name}", "PRIMARY", "registro Global PM: " + name, rel, ident)
            for name in RECORD
        ]
        s.append(
            src(
                reservation,
                "PRIMARY",
                "cópia imutável da autorização (reserva)",
                rel,
                ident,
            )
        )
    s += [
        src(
            "data/platform/v7/radar_origins/v7-5a78ea5d15214e37bcae18f167ffcee3.json",
            "PRIMARY",
            "origem Radar do V1 (arquivo lateral; V1 não sela origem no contexto)",
            "liga o registro V1 aos result.json do Radar recovery-01",
            "HFL-MULTIASSET-GLOBAL-PM-V1",
        ),
        src(
            "scripts/multiasset_global_pm.py",
            "PRIMARY",
            "código do tratamento (hash selado nos contextos V1 e V2)",
            "validador V1",
            "HFL-MULTIASSET-GLOBAL-PM-V1",
        ),
        src(
            "scripts/run_global_pm.py",
            "PRIMARY",
            "código do tratamento (hash selado nos contextos V1 e V2)",
            "runner V1",
            "HFL-MULTIASSET-GLOBAL-PM-V1",
        ),
        src(
            "scripts/multiasset_global_pm_v2.py",
            "PRIMARY",
            "código do tratamento (hash selado no contexto V2)",
            "prompt, schema e validador V2",
            "HFL-MULTIASSET-GLOBAL-PM-V2",
        ),
        src(
            "scripts/run_global_pm_v2.py",
            "PRIMARY",
            "código do tratamento (hash selado no contexto V2)",
            "runner V2; verificadores incident/status",
            "HFL-MULTIASSET-GLOBAL-PM-V2",
        ),
        src(
            "docs/evidence/hfl_global_pm_v2/contracts_v2.json",
            "DERIVED",
            "export dos contratos V1/V2",
            "hashes conferem com os selados nos contextos",
            "HFL-MULTIASSET-GLOBAL-PM-V2",
        ),
        src(
            "docs/evidence/hfl_global_pm_v2/platform_views.json",
            "DERIVED",
            "visões da API (relógio simulado)",
            "status selado x validade",
            "HFL-MULTIASSET-GLOBAL-PM-V2",
        ),
        src(
            "docs/evidence/hfl_global_pm_v2/incident_reproduction.json",
            "DIAGNOSTIC",
            "reprodução V1 + contrafactual em memória",
            "não é segunda inferência; reproduzida de novo na V7.5",
            "HFL-MULTIASSET-GLOBAL-PM-V1",
        ),
        src(
            "docs/evidence/hfl_incident_2026_10_12/forensics.json",
            "DIAGNOSTIC",
            "forense do lote Radar original (bloqueio de rede)",
            "radar-2026-10-09-original: 0/5 comitês; não contado",
            radar_t,
        ),
        src(
            "docs/evidence/hfl_radar_v73/compare_recovery_vs_original.json",
            "DIAGNOSTIC",
            "equivalência econômica dos inputs",
            "recovery-01 x original",
            radar_t,
        ),
        src(
            "docs/evidence/hfl_radar_v73/incident_root_sha256.json",
            "DIAGNOSTIC",
            "hashes dos 45 arquivos do incidente",
            "preservação do lote original",
            radar_t,
        ),
        src(
            f"{OUT}/preservation_before.json",
            "DIAGNOSTIC",
            "snapshot de preservação antes da V7.5",
            "comparado com --since ao final",
            None,
        ),
        src(
            "docs/evidence/hfl_global_pm_v2/qualification.json",
            "SYNTHETIC",
            "índice da qualificação V2 (casos A-F)",
            "FAKE_GLOBAL_PM_NOT_GEMINI; nunca resultado oficial",
            "HFL-MULTIASSET-GLOBAL-PM-V2",
        ),
        src(
            "data/global_pm/hfl_global_pm_v1/v7-3558f0253cf44dd0a00c93d7be73e56f/result.json",
            "SYNTHETIC",
            "registro V1 de demonstração",
            "FAKE_GLOBAL_PM_NOT_GEMINI; nunca resultado oficial",
            "HFL-MULTIASSET-GLOBAL-PM-V1",
        ),
        src(
            "docs/evidence/hfl_global_pm_v2/README.md",
            "INTERPRETATIVE",
            "auditoria manual do texto livre V1 (seção 9)",
            "base do estudo de caso V1",
            "HFL-MULTIASSET-GLOBAL-PM-V1",
        ),
        src(
            "docs/H2_V6_OA1_VALIDATION_SCIENTIFIC_SUMMARY.md",
            "INTERPRETATIVE",
            "delimitação de escopo H2 (não usado em métricas)",
            "fora do escopo da V7.5",
            "H2 v6",
        ),
        src(
            f"{OUT}/METRICS.json",
            "DERIVED",
            "métricas desta consolidação",
            "recalculado por este script",
            None,
        ),
    ]
    return s


def money(tokens_in, tokens_out, rates):
    return str(
        Decimal(tokens_in) * Decimal(rates["input"]) / 10**6
        + Decimal(tokens_out) * Decimal(rates["output"]) / 10**6
    )


def m(
    value,
    definition,
    sources,
    unit=None,
    numerator=None,
    denominator=None,
    caveat=None,
    cls="DERIVED",
):
    return {
        "value": value,
        "unit": unit,
        "definition": definition,
        "numerator": numerator,
        "denominator": denominator,
        "classification": cls,
        "sources": sources,
        "caveat": caveat,
    }


def free_text(resp):
    parts = [resp["global_reasoning"], resp["summary"], *resp["risks"]]
    parts += [a["reasoning"] for a in resp["asset_reasoning"].values()]
    for w in resp.get("watchlist_candidates", []):
        parts += [w["observation"], w["reassessment_condition"]]
    return " ".join(parts).lower()


def metrics():
    out = {}
    res_path = {t: f"{RADAR}/analyses/{t}/{DAY}/result.json" for t in TICKERS}
    radar = {t: load(p) for t, p in res_path.items()}
    calls = [
        r
        for t in TICKERS
        for r in journal(f"{RADAR}/analyses/{t}/{DAY}/provider_journal.jsonl")
    ]
    usage = [r["token_usage"] for r in calls]
    jsrc = [f"{RADAR}/analyses/*/{DAY}/provider_journal.jsonl"]
    rsrc = [f"{RADAR}/analyses/*/{DAY}/result.json"]
    rates = load(V2 + "/result.json")["cost"]["rates_usd_million"]
    reservation = load(RESERVATION)

    out["radar.opinions_completed"] = m(
        sum(r["status"] == "COMPLETED" for r in radar.values()),
        "Pareceres oficiais com status COMPLETED na execução recovery-01.",
        rsrc,
        "pareceres",
        denominator=len(TICKERS),
    )
    out["radar.valid_analyst_votes"] = m(
        sum(r["consensus"]["valid_votes"] for r in radar.values()),
        "Votos técnicos válidos somados nos cinco comitês.",
        rsrc,
        "votos",
        denominator=sum(r["consensus"]["total_analysts"] for r in radar.values()),
    )
    out["radar.provider_calls"] = m(
        {
            "total": len(calls),
            "technical_analyst": sum(r["stage"] == "technical_analyst" for r in calls),
            "risk_manager": sum(r["stage"] == "risk_manager" for r in calls),
            "with_error": sum(
                bool(r.get("error_type") or r.get("error_message")) for r in calls
            ),
            "retries": sum(r.get("retry_count") or 0 for r in calls),
        },
        "Chamadas registradas nos journals do provedor; BBAS3 não chama o Risk LLM (veto determinístico).",
        jsrc,
        "chamadas",
    )
    out["radar.risk_vetoes"] = m(
        sorted(t for t, r in radar.items() if r["risk"]["verdict"] == "VETADO"),
        "Ativos com parecer de risco individual VETADO.",
        rsrc,
        "ativos",
        denominator=len(TICKERS),
    )
    out["radar.per_asset"] = m(
        {
            t: {
                "votes": r["consensus"]["counts"],
                "valid_votes": r["consensus"]["valid_votes"],
                "technical_signal": r["technical_signal"]["signal"],
                "technical_confidence": r["technical_signal"]["confidence"],
                "risk_verdict": r["risk"]["verdict"],
                "risk_source": r["risk_source"],
                "asset_volatility_21": r["risk"]["risk_metrics"]["asset_volatility_21"],
                "rsi": r["features"]["rsi"],
                "bb_upper_gap": r["features"]["bb_upper_gap"],
                "recommendation": r["recommendation"],
            }
            for t, r in radar.items()
        },
        "Votos, sinal agregado, confiança técnica qualitativa, Risk e recomendação final por ativo.",
        rsrc,
        caveat="Confiança técnica é qualitativa (média das confianças dos votos vencedores sobre o total), não probabilidade.",
    )
    out["radar.result_pins_match"] = m(
        all(
            sha(p) == (ROOT / p).with_suffix(".sha256").read_text().strip()
            for p in res_path.values()
        ),
        "SHA-256 de cada result.json igual ao result.sha256 gravado ao lado.",
        rsrc,
        cls="DERIVED",
    )
    reported = [u for u in usage if u["thoughts_tokens"] is not None]
    tin, tout = (
        sum(u["prompt_tokens"] for u in usage),
        sum(u["completion_tokens"] for u in usage),
    )
    tthink = sum(u["thoughts_tokens"] for u in reported)
    out["radar.tokens"] = m(
        {
            "input": tin,
            "output": tout,
            "thoughts_reported": tthink,
            "total": sum(u["total_tokens"] for u in usage),
            "calls_reporting_thoughts": len(reported),
            "calls": len(usage),
        },
        "Tokens informados pelo provedor, somados por chamada nos journals.",
        jsrc,
        "tokens",
        caveat="Pensamento informado em só 1 das 29 chamadas; nas demais o campo está ausente (null), não zero. Os result.json agregados gravam thoughts_tokens=0 nesses comitês (ver errata).",
    )
    out["radar.usd_observed_lower_bound"] = m(
        money(tin, tout + tthink, rates),
        "(entrada x 0,75 + (saída + pensamento informado) x 3,75) / 10^6, preços de 2026-10-11.",
        [*jsrc, V2 + "/result.json"],
        "USD",
        caveat="Piso pelos tokens informados; não é fatura; pensamento não informado pode existir.",
    )
    out["radar.sealed_cost_usd_sum"] = m(
        str(sum(Decimal(str(r["cost_usd"])) for r in radar.values())),
        "Soma do campo cost_usd gravado nos cinco result.json.",
        rsrc,
        "USD",
        caveat="O campo se rotula 'estimated billing'; coincide com o piso acima porque trata pensamento ausente como zero.",
    )
    out["radar.usd_reserved"] = m(
        str(reservation["usd_reserved"]),
        "Reserva conservadora do lote recovery-01.",
        [RESERVATION],
        "USD",
        caveat="Reserva não é custo nem fatura.",
    )
    out["radar.usd_planning_estimate"] = m(
        str(reservation["usd_estimated"]),
        "Estimativa de planejamento do preflight do lote.",
        [RESERVATION],
        "USD",
        caveat="Hipótese de planejamento, não uso observado.",
    )
    claims = [
        load(f"{RADAR}/analyses/{t}/{DAY}/claim.json")["created_at"] for t in TICKERS
    ]
    out["radar.batch_window"] = m(
        {
            "first_claim": min(claims),
            "last_completed": max(r["completed_at"] for r in radar.values()),
        },
        "Janela do lote pago do Radar (claim mais antigo → último parecer).",
        rsrc,
        cls="DERIVED",
        caveat="Inferência em 12/10 sobre dados congelados da sessão de 09/10.",
    )
    forensics = load("docs/evidence/hfl_incident_2026_10_12/forensics.json")
    out["radar.original_incident"] = m(
        {
            "committees": forensics["job_outcome"]["committees"],
            "committees_completed": forensics["job_outcome"]["committees_completed"],
            "job_started_at": forensics["job"]["started_at"],
            "usd_reserved_uncertain": str(forensics["reservation"]["usd_reserved"]),
        },
        "Lote original de 12/10 02:59 bloqueado pelo guard offline; nenhum comitê válido.",
        ["docs/evidence/hfl_incident_2026_10_12/forensics.json"],
        cls="DIAGNOSTIC",
        caveat="Não contado como comitê válido em nenhuma métrica.",
    )

    radar_hash = {t: sha(p) for t, p in res_path.items()}
    gpm = {}
    for name, root in (("v1", V1), ("v2", V2)):
        res, ctx = load(root + "/result.json"), load(root + "/context.json")
        auth, rec = (
            load(root + "/authorization.json"),
            journal(root + "/private/provider_journal.jsonl"),
        )
        resp, val = res["response"], res["validation"]
        gpm[name] = (res, ctx)
        srcs = [f"{root}/result.json", f"{root}/context.json"]
        weights = sum(Decimal(w) for w in resp["target_weights"].values()) + Decimal(
            resp["target_cash_weight"]
        )
        vetoed = [t for t, o in ctx["opinions"].items() if o["risk_verdict"] == "VETADO"]
        u = res["tokens"]
        sealed = ctx["contracts"]["sources_sha256"]
        mine = [p for p in sealed if "global_pm" in p]
        out[f"gpm_{name}.identity"] = m(
            {
                "treatment": res["identity"],
                "record_id": res["record_id"],
                "context_sha256": ctx["sha256"],
                "contracts_sha256": ctx["contracts"]["sha256"],
                "prompt_version": ctx["contracts"]["prompt_version"],
                "validation_policy": val.get("validation_policy"),
                "mode": res["mode"],
                "planner": res["planner"],
                "requested_model": rec[0]["requested_model"],
                "resolved_model": rec[0]["resolved_model"],
                "options": rec[0]["requested_options"],
                "decision_session": resp["decision_session"],
                "radar_origin_sealed_in_context": ctx.get("radar_origin") is not None,
            },
            "Identidade, contrato, modelo e sessão do registro.",
            [*srcs, f"{root}/private/provider_journal.jsonl"],
            cls="PRIMARY",
        )
        out[f"gpm_{name}.outcome"] = m(
            {
                "status": res["status"],
                "errors": [e["code"] for e in val["errors"]],
                "financial_validation_valid": val["financial_validation"]["valid"],
                "risk_projected": val["financial_validation"]["risk_projected"]["status"],
                "operations": len(resp["operations"]),
                "initial_capital": val["projection"]["initial_capital"],
                "target_cash_weight": resp["target_cash_weight"],
                "target_weights": resp["target_weights"],
                "weights_plus_cash": str(weights),
                "projected_exposure": val["projection"]["exposure"],
                "portfolio_changed": res["portfolio_changed"],
                "execution_enabled": res["execution_enabled"],
                "not_selected": resp["not_selected"],
                "deferred_field": resp.get(
                    "deferred_opportunities", resp.get("settlement_deferred_operations")
                ),
                "watchlist": [w["ticker"] for w in resp.get("watchlist_candidates", [])],
            },
            "Status selado, erros, validação financeira V5 e conteúdo estrutural da proposta.",
            srcs,
            cls="PRIMARY",
        )
        out[f"gpm_{name}.integrity"] = m(
            {
                "opinion_refs_equal_context": resp["opinion_refs"]
                == {t: o["sha256"] for t, o in ctx["opinions"].items()},
                "context_opinions_point_to_radar_results": all(
                    ctx["opinions"][t]["result_sha256"] == radar_hash[t] for t in TICKERS
                ),
                "vetoed": vetoed,
                "veto_respected": all(
                    Decimal(resp["target_weights"][t]) == 0
                    and not any(o.get("ticker") == t for o in resp["operations"])
                    for t in vetoed
                ),
                "weights_sum_to_one": weights == 1,
                "journal_sha256_matches_result": sha(
                    f"{root}/private/provider_journal.jsonl"
                )
                == res["journal_sha256"],
                "journal_calls": len(rec),
                "journal_response_equals_result": rec[0]["validated_response"] == resp,
                "treatment_sources_unchanged": {p: sha(p) == sealed[p] for p in mine},
            },
            "Conferências determinísticas de hashes, referências, veto e soma de pesos.",
            [*srcs, f"{root}/private/provider_journal.jsonl", *rsrc],
            cls="DERIVED",
        )
        lower = money(u["prompt_tokens"], u["completion_tokens"], rates)
        out[f"gpm_{name}.usage"] = m(
            {
                "input": u["prompt_tokens"],
                "output": u["completion_tokens"],
                "thoughts": u["thoughts_tokens"],
                "total": u["total_tokens"],
                "input_plus_output_equals_total": u["prompt_tokens"]
                + u["completion_tokens"]
                == u["total_tokens"],
                "usd_observed_lower_bound": lower,
                "usd_reserved": auth["usd_reserved"],
                "usd_planning_estimate": auth["preflight"]["estimate"]["usd_estimated"],
                "input_bytes_estimated": auth["preflight"]["estimate"][
                    "input_bytes_estimated"
                ],
                "cost_usd_recorded": res["cost_usd"],
                "duration_ms": rec[0]["duration_ms"],
                "attempts": rec[0]["attempt_count"],
            },
            "Tokens informados (usageMetadata), piso monetário, reserva e duração da única chamada.",
            [
                *srcs,
                f"{root}/authorization.json",
                f"{root}/private/provider_journal.jsonl",
            ],
            "tokens / USD",
            caveat="thoughtsTokenCount ausente: pensamento não informado, não zero. Piso ≠ fatura; reserva ≠ custo. Uma amostra por tratamento.",
        )
        out[f"gpm_{name}.timeline"] = m(
            {
                "market_session_valuation": val["financial_validation"]["checked_at"],
                "context_created_at": ctx["created_at"],
                "claim_created_at": load(root + "/claim.json")["created_at"],
                "provider_call_started_at": rec[0]["started_at"],
                "validation_at": res["validation_at"],
                "expires_at": ctx["expires_at"],
            },
            "Separação entre o instante de mercado, a preparação, a inferência e a validação.",
            [*srcs, f"{root}/claim.json", f"{root}/private/provider_journal.jsonl"],
            cls="PRIMARY",
        )
        out[f"gpm_{name}.free_text_terms"] = m(
            {term: term in free_text(resp) for term in TERMS},
            "Presença literal de termos sensíveis no texto livre (reasoning, global_reasoning, risks, summary, watchlist).",
            srcs,
            cls="DERIVED",
            caveat="Proxy lexical; não substitui a auditoria manual nem valida o texto.",
        )

    resp2, ctx2 = gpm["v2"][0]["response"], gpm["v2"][1]
    cited = [
        (t, k, v)
        for t, a in resp2["asset_reasoning"].items()
        for k, v in a["cited_metrics"].items()
    ]

    def agrees(t, k, v):
        source = Decimal(ctx2["verifiable_metrics"][t][k])
        return source.quantize(Decimal(v), rounding=ROUND_HALF_EVEN) == Decimal(v)

    out["gpm_v2.cited_metrics"] = m(
        {"cited": len(cited), "agree_with_context": sum(agrees(*c) for c in cited)},
        "Métricas citadas em cited_metrics que conferem com verifiable_metrics (half-even na precisão citada).",
        [V2 + "/result.json", V2 + "/context.json"],
        "métricas",
    )
    out["gpm_v2.watchlist_signals_match"] = m(
        all(
            w["radar_signal"] == ctx2["opinions"][w["ticker"]]["recommendation"]
            for w in resp2["watchlist_candidates"]
        ),
        "radar_signal de cada observação igual à recomendação final do parecer.",
        [V2 + "/result.json", V2 + "/context.json"],
    )
    out["gpm.same_opinions_v1_v2"] = m(
        gpm["v1"][0]["response"]["opinion_refs"] == resp2["opinion_refs"],
        "V1 e V2 receberam os mesmos cinco pareceres (mesmos hashes).",
        [V1 + "/result.json", V2 + "/result.json"],
        caveat="Mesmas entradas de Radar; snapshots, prompts, schemas e contratos diferentes.",
    )
    u1, u2 = gpm["v1"][0]["tokens"], gpm["v2"][0]["tokens"]
    out["gpm.token_delta_v2_minus_v1"] = m(
        {
            k: u2[k] - u1[k]
            for k in ("prompt_tokens", "completion_tokens", "total_tokens")
        },
        "Diferença bruta de tokens V2 - V1.",
        [V1 + "/result.json", V2 + "/result.json"],
        "tokens",
        caveat="Duas chamadas únicas, contratos diferentes, temperatura 1.0: não é experimento controlado de eficiência.",
    )
    records = sorted(glob.glob(str(ROOT / "data/global_pm/*/*/result.json")))
    planners = [load(Path(p).relative_to(ROOT).as_posix())["planner"] for p in records]
    real = [
        Path(p).parent.name
        for p, pl in zip(records, planners)
        if pl == "GEMINI_GLOBAL_PM"
    ]
    out["gpm.records_by_planner"] = m(
        {
            "real_gemini": len(real),
            "real_ids": real,
            "synthetic": len(planners) - len(real),
        },
        "Registros Global PM com result.json, separados por planner (GEMINI_GLOBAL_PM x FAKE_GLOBAL_PM_NOT_GEMINI).",
        ["data/global_pm/*/*/result.json"],
        "registros",
        caveat="Os sintéticos são qualificação/demonstração e nunca entram nas métricas de resultado.",
    )
    out["gpm.real_outcomes"] = m(
        {
            "VALID_PROPOSAL": 1 if gpm["v2"][0]["status"] == "VALID_PROPOSAL" else 0,
            "REJECTED_BY_VALIDATOR": 1
            if gpm["v1"][0]["status"] == "REJECTED_BY_VALIDATOR"
            else 0,
        },
        "Desfecho das inferências reais (uma por tratamento).",
        [V1 + "/result.json", V2 + "/result.json"],
        "inferências",
        denominator=len(real),
        caveat="n=2, tratamentos distintos: nenhuma taxa de aprovação é estimável ou generalizável.",
    )
    v1ctx = gpm["v1"][1]
    out["gpm_v1.itub4_close_inside_upper_band"] = m(
        Decimal(str(v1ctx["opinions"]["ITUB4"]["features"]["bb_upper_gap"])) < 0,
        "bb_upper_gap de ITUB4 negativo (fechamento abaixo da banda superior), contrariando 'rompimento' no texto V1.",
        [V1 + "/context.json"],
    )
    return out


def build():
    data = {
        "identity": "HFL-V75-SCIENTIFIC-CONSOLIDATION",
        "schema_version": 1,
        "metrics": metrics(),
    }
    write(f"{OUT}/METRICS.json", data)
    manifest = {
        "identity": "HFL-V75-SCIENTIFIC-CONSOLIDATION",
        "schema_version": 1,
        "classes": CLASSES,
        "note": "O manifesto não contém o próprio hash. Documentos .md da V7.5 são fixados pelo commit Git.",
        "sources": [
            {**s, "sha256": sha(s["path"]), "bytes": (ROOT / s["path"]).stat().st_size}
            for s in sources()
        ],
        "provenance": PROVENANCE,
    }
    write(f"{OUT}/EVIDENCE_MANIFEST.json", manifest)
    return {"written": [f"{OUT}/METRICS.json", f"{OUT}/EVIDENCE_MANIFEST.json"]}


def write(path, data):
    # ponytail: LF bytes so the Windows working copy matches the committed blob.
    (ROOT / path).write_bytes(
        (json.dumps(data, ensure_ascii=False, indent=1) + "\n").encode()
    )


def pt(value):
    return (
        f"{value:,}".replace(",", ".")
        if isinstance(value, int)
        else value.replace(".", ",")
    )


def doc_divergences(ms):
    for doc, ids in DOC_FACTS.items():
        text = (ROOT / OUT / doc).read_text(encoding="utf-8")
        for i in ids:
            value = ms[i]["value"]
            for key in (
                "input",
                "output",
                "total",
                "usd_observed_lower_bound",
                "usd_reserved",
            ):
                if key in value and pt(value[key]) not in text:
                    yield f"{doc}: {i}.{key} = {pt(value[key])}"


def check():
    report = {
        "missing": [],
        "violations": [],
        "operational_changes": [],
        "metric_divergences": [],
        "doc_divergences": [],
    }
    for s in load(f"{OUT}/EVIDENCE_MANIFEST.json")["sources"]:
        if not (ROOT / s["path"]).exists():
            report["missing"].append(s["path"])
        elif sha(s["path"]) != s["sha256"]:
            key = (
                "operational_changes"
                if s["immutability"] == "OPERATIONAL"
                else "violations"
            )
            report[key].append(s["path"])
    if not report["missing"]:
        expected = load(f"{OUT}/METRICS.json")["metrics"]
        now = json.loads(json.dumps(metrics(), ensure_ascii=False))
        report["metric_divergences"] = sorted(
            k for k in expected.keys() | now.keys() if expected.get(k) != now.get(k)
        )
        report["doc_divergences"] = list(doc_divergences(expected))
    report["ok"] = not any(
        report[k]
        for k in ("missing", "violations", "metric_divergences", "doc_divergences")
    )
    return report


def main():
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("command", nargs="?", choices=("check", "build"), default="check")
    args = parser.parse_args()
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    result = build() if args.command == "build" else check()
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result.get("ok", True) else 1


if __name__ == "__main__":
    sys.exit(main())
