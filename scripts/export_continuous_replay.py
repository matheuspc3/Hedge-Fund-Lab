"""Export the campaign's existing receipts; no inference or financial mutations."""
import argparse
import csv
import json
import sqlite3
from hashlib import sha256
from pathlib import Path

import continuous_replay as c
from report_multiasset_replay import usage_of

LABELS = {"MULTIAGENT": "Multiagentes", "BUY_HOLD": "Buy & Hold", "SMA_50_200": "SMA 50/200", "BOLLINGER_20_2": "Bollinger 20/2", "EQUAL_WEIGHT_63": "Equal Weight", "MIN_VARIANCE_252_63": "Mínima Variância"}


def audit_budget(root):
    """Reconcile physical attempts, exact envelopes and the serial reservation peak."""
    with c.closing(sqlite3.connect(c.budget_path(root).resolve().as_uri() + "?mode=ro", uri=True)) as conn:
        rows = conn.execute("SELECT id,reserve,charge,state,raw,sha,metadata FROM attempts ORDER BY rowid").fetchall()
    groups, models = {}, set()
    total = peak = known = uncertain = c.b.ZERO
    tokens = dict.fromkeys(("prompt_tokens", "completion_tokens", "thoughts_tokens", "total_tokens"), 0)
    for key, bound, charge, state, raw, digest, text in rows:
        reserve, cost, meta = c.b.dec(bound), c.b.dec(charge), json.loads(text)
        assert total + reserve <= c.b.dec("34.78"), "reservation would exceed the aggregate ceiling"
        peak = max(peak, total + reserve)
        total += cost
        assert c.b.ZERO <= cost <= reserve
        identity = (meta["bank"], meta["slot"], meta["sequence"])
        group = groups.setdefault(identity, [])
        group.append((meta, raw is not None))
        assert key == f"{meta['bank']}/{meta['slot']}/{meta['sequence']}/{meta['attempt']}"
        usage = None
        if raw is not None:
            assert sha256(raw).hexdigest() == digest, "physical envelope hash differs"
            try:
                payload = json.loads(raw)
            except (json.JSONDecodeError, UnicodeDecodeError):
                payload = None
            if isinstance(payload, dict):
                provider = payload.get("usageMetadata") or {}
                if isinstance(provider, dict):
                    usage = usage_of({"token_usage": {target: provider.get(source) for source, target in {"promptTokenCount": "prompt_tokens", "candidatesTokenCount": "completion_tokens", "thoughtsTokenCount": "thoughts_tokens", "totalTokenCount": "total_tokens"}.items()}})
                if payload.get("modelVersion"):
                    models.add(payload["modelVersion"])
        if state == "KNOWN":
            assert usage is not None
            expected = (c.b.dec(usage["prompt_tokens"]) * c.b.dec("0.75") + c.b.dec(usage["completion_tokens"] + usage["thoughts_tokens"]) * c.b.dec("3.75")) / 1000000
            assert expected == cost, "physical provider usage and charged estimate differ"
            known += cost
            for name in tokens:
                tokens[name] += usage[name]
        else:
            assert state in ("IN_FLIGHT", "UNKNOWN_TRANSPORT", "UNKNOWN_USAGE") and cost == reserve
            uncertain += cost
    for attempts in groups.values():
        assert len(attempts) <= 2
        assert len({meta["request_identity"] for meta, _ in attempts}) == 1
        assert sum(has_raw for _, has_raw in attempts) <= 1, "more than one consumed response for a logical vote"
    result = {"status": "PASS", "physical_attempts": len(rows), "logical_calls_with_transport": len(groups), "retried_logical_calls": sum(len(v) > 1 for v in groups.values()), "max_attempts_per_logical_call": max((len(v) for v in groups.values()), default=0), "known_estimated_usd": str(known), "uncertain_and_inflight_reserved_usd": str(uncertain), "exposure_usd": str(total), "max_exposure_before_http_usd": str(peak), "peak_basis": "Serial dispatch order; reconciled earlier usage plus full unknown/in-flight reservations", "known_provider_tokens": tokens, "resolved_models": sorted(models), "verification_source_sha256": c.b.sha_file(__file__)}
    c.radar.write(root / "budget_audit.json", c.b.sealed(result))
    return result


def table(path, rows):
    if not rows:
        return
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(dict.fromkeys(k for row in rows for k in row)))
        writer.writeheader()
        writer.writerows({k: json.dumps(v, ensure_ascii=False, sort_keys=True) if isinstance(v, (list, dict)) else v for k, v in row.items()} for row in rows)


def export(root=c.RUN_ROOT):
    campaign = c.r.checked(c.campaign_path(root))
    c.manual.ROOT = root / "book"
    daily, analyses, managers, events, calls = [], {}, {}, {}, []
    for day in campaign["sessions"]:
        marker = root / "sessions" / day / "day.json"
        ref = root / "references" / (day + ".json")
        if not ref.exists():
            break
        value = c.r.checked(marker) if marker.exists() else {**c.r.checked(ref), "status": "REFERENCES_ONLY"}
        daily.append(value)
        for ticker in c.radar.EXAMPLES:
            folder = root / "sessions" / day / "radar" / ticker
            for kind in ("result", "failure"):
                if (folder / (kind + ".json")).exists():
                    analyses.setdefault(day, {})[ticker] = c.r.checked(folder / (kind + ".json"))
        path = root / "sessions" / day / "manager/proposal.json"
        if path.exists():
            managers[day] = c.r.checked(path)
    with c.closing(c.manual.connect()) as conn:
        for wallet in c.manual.catalog(conn):
            events[wallet["strategy"]] = c.manual.events(conn, wallet["id"])
    for path in sorted((root / "sessions").glob("**/calls.sqlite")):
        # Use SQLite read-only URI; preserve raw envelopes in the original call banks.
        with c.closing(sqlite3.connect(path.as_uri() + "?mode=ro", uri=True)) as conn:
            for slot, sequence, record, record_sha, raw, raw_sha in conn.execute("SELECT slot,sequence,record,record_sha,raw,raw_sha FROM calls ORDER BY sequence"):
                if record and sha256(record.encode()).hexdigest() != record_sha or raw and sha256(raw).hexdigest() != raw_sha:
                    raise ValueError("export_call_bank_integrity_failed")
                calls.append({"bank": str(path.relative_to(root)).replace("\\", "/"), "slot": slot, "sequence": sequence, "record": json.loads(record) if record else None})
    out = root / "exports"
    out.mkdir(exist_ok=True)
    market = c.r.checked(c.ROOT / "inputs/market.json")["assets"]
    c.market.ROOT = c.ROOT / "inputs/market"
    entitlements = {d["day"]: {} for d in daily}
    for strategy, history in events.items():
        wallet = c.manual.replay(history)
        for d in daily:
            if strategy not in d["valuation"]:
                continue
            items = [e for e in c.dividends.entitlements(wallet, d["day"]) if not e["estimate"]]
            received, receivable = c.dividends.on(items, d["day"])
            assert receivable == c.b.dec(d["valuation"][strategy]["receivable"])
            assert received == sum((c.b.dec(p["net"]) for p in wallet["dividends"] if p["payment_date"] <= d["day"]), c.b.ZERO)
            entitlements[d["day"]][strategy] = items
    budget_audit = audit_budget(root)
    doc = {"campaign": campaign, "labels": LABELS, "days": daily, "analyses": analyses, "managers": managers, "events": events, "market": market, "entitlements": entitlements, "budget": c.Budget(c.budget_path(root)).summary(), "budget_audit": budget_audit, "completed": (root / "status.json").exists() and c.r.checked(root / "status.json")["state"] == "COMPLETED"}
    c.radar.write(out / "explorer.json", c.b.sealed(doc))
    c.radar.write(out / "calls.json", c.b.sealed({"logical_calls": calls}))
    table(out / "daily.csv", [{"session": d["day"], "status": d["status"], "strategy": s, **v} for d in daily for s, v in d["valuation"].items()])
    operations, decisions, dividends = [], [], []
    for strategy, history in events.items():
        for event in history:
            kind, req = event["request"]["kind"], event["request"]
            common = {"strategy": strategy, "event_id": event["id"], "sha256": event["sha256"], "recorded_at": event["recorded_at"]}
            if kind == "TRADE":
                operations.append({**common, **req["trade"], "source": event.get("source")})
            elif kind == "DIVIDEND":
                dividends.append({**common, **req["dividend"], "source": event.get("source")})
            elif kind == "RULE_DECISION":
                decisions.append({**common, **event["source"]})
    table(out / "operations.csv", operations)
    table(out / "decisions.csv", decisions)
    table(out / "dividends.csv", dividends)
    table(out / "calls.csv", [{"bank": v["bank"], "slot": v["slot"], "sequence": v["sequence"], **(v["record"] or {})} for v in calls])
    usages = [u for item in calls if item["record"] and (u := usage_of(item["record"])) is not None]
    summary = {"daily_sessions": len(daily), "daily_wallet_states": sum(len(d["valuation"]) for d in daily), "operations_including_initial": len(operations), "dividends": len(dividends), "rule_decisions": len(decisions), "logical_calls": len(calls), "known_tokens": budget_audit["known_provider_tokens"], "calls_with_reconciled_trace_usage": len(usages), "resolved_models": budget_audit["resolved_models"], "export_sha256": c.b.sha_file(out / "explorer.json"), "budget": doc["budget"], "budget_audit": budget_audit}
    c.radar.write(out / "manifest.json", c.b.sealed(summary))
    if len(daily) == len(campaign["sessions"]) and set(daily[-1]["valuation"]) == set(c.STRATEGIES):
        br = lambda value, places=2: format(c.b.dec(value), f",.{places}f").translate(str.maketrans(",.", ".,"))
        lines = ["# Campanha contínua de seis carteiras — abril a novembro de 2026", "", "DP-35/36 / REPLAY-01. Reconstrução exploratória produzida agora; não é evidência prospectiva ou demonstração de superioridade.", "", f"Período {campaign['sessions'][0]}–{campaign['sessions'][-1]}, {len(daily)} pregões. R$ 100.000 independentes por carteira, cesta inicial comum, ações inteiras, custos posteriores de 0,03%, proventos líquidos por componente em caixa no pagamento. As cinco referências foram concluídas antes da inferência.", "", "| Carteira | Patrimônio final R$ | Retorno % | Caixa R$ | Recebíveis R$ | Custos R$ | Operações após entrada |", "|---|---:|---:|---:|---:|---:|---:|"]
        for strategy in c.STRATEGIES:
            v = daily[-1]["valuation"][strategy]
            trades = sum(op["strategy"] == strategy for op in operations) - 5
            lines.append(f"| {LABELS[strategy]} | {br(v['equity'])} | {br(v['return_pct'],4)} | {br(v['cash'])} | {br(v['receivable'])} | {br(v['costs'])} | {trades} |")
        budget = doc["budget"]
        gaps = [d["day"] for d in daily if d.get("status") != "COMPLETED"]
        lines.extend(["", f"Análises diárias completas: {len(daily)-len(gaps)}/{len(daily)}. Lacunas: {', '.join(gaps) or 'nenhuma'}. Uma falha preserva a posição; não se fabrica HOLD nem se substitui resposta inválida.", "", f"Orçamento agregado US$ {budget['cap_usd']}, {budget['physical_attempts']} tentativas HTTP. Uso conhecido estimado US$ {budget['known_estimated_usd']}; reserva adicional incerta US$ {budget['uncertain_and_inflight_reserved_usd']}; exposição total US$ {budget['exposure_usd']}. Inclui todas as retomadas/retries desta campanha; não é fatura ou confirmação de saldo promocional.", "", "Verificação: checks.json reconstrói estados diários, entradas iguais, fills RAW na abertura, custos de 0,03%, causalidade das janelas, 252 retornos de aquecimento e todos os componentes de proventos elegíveis, sem caixa antecipado. A preservação dos pilotos e do livro local de outubro é conferida por hashes.", "", "SMA 50/200 e Bollinger 20/2: regras atuais da aplicação, parcelas independentes de 20%. Equal/Mínima: rebalanceamento a cada 63 pregões, Mínima com 252 retornos e sem shorts, mesmo objetivo e restrições do SLSQP, com escala normalizada por uma constante positiva; resultados/fallbacks preservados. Compras na abertura usam o mesmo ajuste proporcional ao caixa da Multiagentes. Buy & Hold/regras não reinvestem proventos. O gestor mantém o fluxo atual e pode realocar o caixa recebido sob seus sinais/gates."])
        if all(d["valuation"]["EQUAL_WEIGHT_63"]["equity"] == d["valuation"]["MIN_VARIANCE_252_63"]["equity"] for d in daily):
            lines.extend(["", "Equal Weight e Mínima Variância produziram curvas idênticas. Os resultados do SLSQP permaneceram nos pesos iniciais iguais com os defaults existentes; isso não demonstra que a solução seja o mínimo global exato. Nenhum parâmetro do otimizador foi ajustado após observar o retorno."])
        lines.extend(["", "Limites: dados/fatores/proventos reconstituídos agora, sem arquivo point-in-time; cutoff declarado de março/2026 não certifica ausência de contaminação; alias Gemini não imutável; PREABE diário é proxy da abertura, sem microestrutura, spread, impacto ou liquidação D+2; caixa não rende. A prévia intradiária e o alerta de tese velha não foram reconstruídos. JCP usa a hipótese de 15% do contrato atual, sem exceções fiscais. IA decide antes da abertura de D0 com referência anterior; regras começam no fechamento de D0. API em USD separada dos custos de negociação em BRL.", "", "Os dois pilotos anteriores, outubro oficial, H2 e produção Railway permanecem separados. A coleta do Railway foi consultada somente em leitura e já estava atualizada até 12/11; o checkout do PC era a cópia pré-migração. Os 16 snapshots recentes conferem com a preparação.", "", "Evidências e exportações: `data/cache/continuous-replay/april-november-2026-flash/`; manifestos versionados, inputs/CSV, SQLite de livro/chamadas/orçamento, recibos por sessão, respostas brutas e `qualified-v2/exports/{explorer,calls}.json`, daily/operations/decisions/dividends/calls.csv. Reparos pré-pagos de identidade dos componentes JCP e de escala numérica da Mínima Variância documentados no inventário, sem reescrever evidências diagnósticas.", "", "Próxima etapa: explorar os resultados na interface e usar o relato descritivo no TCC; qualquer nova campanha ou ajuste estratégico requer escopo próprio.", ""])
        final = daily[-1]["valuation"]
        difference = c.b.dec(final["MULTIAGENT"]["equity"]) - c.b.dec(final["BUY_HOLD"]["equity"])
        hard = sum(a.get("risk_source") == "HARD_ASSET_VOLATILITY_RULE" for values in analyses.values() for a in values.values())
        lines[5:5] = [f"A Multiagentes terminou R$ {br(abs(difference))} {'abaixo' if difference < 0 else 'acima'} do Buy & Hold. O maior patrimônio final nesta execução foi de {LABELS[max(final, key=lambda k: c.b.dec(final[k]['equity']))]}. A comparação não identifica causalidade nem valida superioridade fora desta trajetória.", ""]
        lines.extend(["", f"Auditoria do orçamento PASS: {budget_audit['logical_calls_with_transport']} chamadas lógicas, {budget_audit['retried_logical_calls']} retries, máximo {budget_audit['max_attempts_per_logical_call']} tentativas por chamada, no máximo uma resposta consumida por voto. Pico reconstruído antes de HTTP: US$ {budget_audit['max_exposure_before_http_usd']}. {hard} vetos determinísticos dispensaram a chamada de risco; não foram lacunas de análise.", "", f"Tokens conhecidos: {summary['known_tokens']['prompt_tokens']} de entrada + {summary['known_tokens']['completion_tokens']} de saída + {summary['known_tokens']['thoughts_tokens']} de thinking = {summary['known_tokens']['total_tokens']}. Versão devolvida: {', '.join(summary['resolved_models'])}; esse texto não certifica checkpoint imutável.", "", "A inferência continuou durante a interrupção do Codex e terminou em 13/11/2026 às 22:28 (São Paulo), sem segunda instância nem reset. Reprodutibilidade da análise usa os envelopes/votos persistidos; novas chamadas ao alias estocástico não garantem respostas iguais.", ""])
        target = root / "report.md" if campaign["mode"] == "OFFLINE_TEST_ONLY" else c.PROJECT / "reports/replay_continuo_2026-04_2026-11.md"
        target.write_text("\n".join(lines), encoding="utf-8")
    return summary


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=c.RUN_ROOT)
    print(json.dumps(export(parser.parse_args().root.resolve()), indent=2))
