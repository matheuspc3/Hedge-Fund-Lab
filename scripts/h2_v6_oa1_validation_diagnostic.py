"""Diagnóstico retrospectivo EXPLORATÓRIO da Validation provisória H2-V6-OA1.

Não é resultado científico, não altera protocolo e não seleciona estratégia.
Só lê os artifacts selados em ``data/runs/h2_v6_provisional/VALIDATION``
(SQLite em modo ``immutable``): nenhuma chamada ao provedor, nenhum snapshot
(ele contém o período do Final Test), nenhum participante, replay ou escrita.
Os fechamentos vêm da curva selada do Buy & Hold (caixa residual ~1e-12).
Cada achado de ``docs/H2_V6_OA1_VALIDATION_DIAGNOSTIC.md`` é um assert aqui.

Uso: ``.venv\\Scripts\\python.exe -B scripts/h2_v6_oa1_validation_diagnostic.py``
"""

import collections
import contextlib
import hashlib
import json
import math
import sqlite3
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.backtesting.metrics import performance_metrics  # noqa: E402

VAL = ROOT / "data/runs/h2_v6_provisional/VALIDATION"
CHECKPOINT = ROOT / "docs/evidence/h2_v6_provisional/VALIDATION_PROVISIONAL_CHECKPOINT.json"
SLOTS = ("L01", "L02", "L03")
BENCH = ("buy_and_hold", "sma_regime_h2_proposed", "bollinger_state_h2_proposed")
RATE = {0: 0.00032, 5: 0.00082, 10: 0.00132, 20: 0.00232}  # spread + 0,032%


def sha(data):
    return hashlib.sha256(data).hexdigest()


def run(name, spread=5):
    return VAL / "runs" / f"H2-V6-OA1-VALIDATION-{name}{'' if spread == 5 else f'-cost-{spread}'}-2808fe83f2a4"


def jsonl(path):
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]


def equity(name, spread=5):
    # round_trip: o parser padrão do pandas erra 1 ulp e gera ruído de 1e-14 nas métricas.
    frame = pd.read_csv(run(name, spread) / "equity.csv", index_col="date", parse_dates=True, float_precision="round_trip")
    return frame["equity"]


def trades(name, spread=5):
    return pd.read_csv(run(name, spread) / "trades.csv", parse_dates=["date"], float_precision="round_trip")


def canon(x):  # src.agents.features.canonical_number
    r = round(float(x), 6)
    return 0.0 if r == 0 else r


def section(title):
    print(f"\n## {title}")


# ── 0. Integridade ─────────────────────────────────────────────────
section("0. Integridade dos artifacts selados")
checkpoint = json.loads(CHECKPOINT.read_text(encoding="utf-8"))
pinned = {**checkpoint["artifacts_sha256"], **checkpoint["files_sha256"]}
bad = [rel for rel, h in pinned.items() if sha((VAL / rel.replace("\\", "/")).read_bytes()) != h]
assert not bad, bad
release = json.loads((VAL / "validation_release.sha256.json").read_text())["sha256"]
assert sha((VAL / "validation_release.json").read_bytes()) == release
print(f"{len(pinned)} arquivos do checkpoint conferem; validation_release.json confere")

# ── Fechamentos e reconstrução das curvas ──────────────────────────
bh_trade = trades("buy_and_hold").iloc[0]
bh_cash = 100000.0 - bh_trade.quantity * bh_trade.price - bh_trade.cost
close = (equity("buy_and_hold").loc[bh_trade.date:] - bh_cash) / bh_trade.quantity
sessions = equity("buy_and_hold").index
prev = dict(zip(sessions[1:], sessions[:-1]))
names = [(s, 5) for s in SLOTS] + [(b, c) for b in BENCH for c in (0, 5, 10, 20)]
for name, spread in names:
    cash, qty, worst = 100000.0, 0.0, 0.0
    tr, eq = trades(name, spread), equity(name, spread)
    by_day = dict(list(tr.groupby("date")))
    for day in sessions:
        for _, t in by_day.get(day, tr.iloc[:0]).iterrows():
            notional = t.quantity * t.price
            assert abs(t.cost - notional * RATE[spread]) < 1e-9
            cash += -(notional + t.cost) if t.type == "BUY" else notional - t.cost
            qty += t.quantity if t.type == "BUY" else -t.quantity
        value = cash + (qty * close[day] if abs(qty) > 1e-9 else 0.0)
        worst = max(worst, abs(value / eq[day] - 1))
    assert worst < 1e-12, (name, spread, worst)
print(f"15 curvas reconstruídas de trades + fechamentos (erro relativo < 1e-12); caixa residual B&H {bh_cash:.1e}")

calls = {s: jsonl(run(s) / "llm_calls.jsonl") for s in SLOTS}
dec = {s: {d["decision_session"]: d for d in jsonl(run(s) / "decisions.jsonl")} for s in SLOTS}
features = {c["decision_session"]: json.loads(c["user_prompt"])["features"]
            for c in calls["L01"] if c["stage"] == "technical_analyst" and c["analyst_id"] == 1}

# ── 1. Timeline das operações ──────────────────────────────────────
section("1. Timeline das ordens executadas (decisão no fechamento de t, execução na abertura de t+1)")
for slot in ("L01", "L02"):
    eq = equity(slot)
    by_session = collections.defaultdict(list)
    for c in calls[slot]:
        by_session[c["decision_session"]].append(c)
    print(f"\n{slot}{' (= L03, bytes idênticos)' if slot == 'L02' else ''}")
    print("exec       | lado | preço    | quantidade   | custo  | patrim.fech | decisão    | votos C/V/M | PM (seq)")
    for _, t in trades(slot).iterrows():
        d0 = str(prev[t.date].date())
        v = dec[slot][d0]["vote_counts"]
        pm = next(c for c in by_session[d0] if c["stage"] == "portfolio_manager")
        print(f"{t.date.date()} | {t.type:4s} | {t.price:8.4f} | {t.quantity:12.6f} | {t.cost:6.2f} | {eq[t.date]:11.2f} |"
              f" {d0} | {v['COMPRA']}/{v['VENDA']}/{v['MANTER']}       | {pm['sequence']}")
    tr = trades(slot)
    print("ciclo (exec)            | preço ent→saída   | var.preço | P&L líquido | custos | sessões")
    for i in range(0, len(tr), 2):
        b, s = tr.iloc[i], tr.iloc[i + 1]
        net = b.quantity * (s.price - b.price) - b.cost - s.cost
        held = int(((sessions >= b.date) & (sessions <= s.date)).sum()) - 1
        print(f"{b.date.date()}→{s.date.date()} | {b.price:.4f}→{s.price:.4f} | {s.price / b.price - 1:+7.2%} |"
              f" {net:+10.2f} | {b.cost + s.cost:6.2f} | {held}")
    assert abs(sum(tr.cost) - json.loads((run(slot) / "manifest.json").read_text())["total_transaction_cost"]) < 1e-9

# ── 2. Exposição ────────────────────────────────────────────────────
section("2. Exposição (posição no fechamento das 247 sessões de decisão)")
lbh = np.log(equity("buy_and_hold") / equity("buy_and_hold").shift(1)).dropna()


def states(name):
    kinds, held, out = dict(zip(trades(name).date, trades(name).type)), False, {}
    for day in sessions:
        kind = kinds.get(day)
        held = {"BUY": True, "SELL": False}.get(kind, held)
        out[day] = {"BUY": "entry", "SELL": "exit"}.get(kind, "long" if held else "cash")
    return pd.Series(out)


for name in (*SLOTS, *BENCH):
    st = states(name)
    long = st[sessions[:-1]].isin(["long", "entry"])
    print(f"{name:28s} comprado {long.sum():3d}/247 ({long.mean():.1%})  caixa {(~long).sum():3d}/247")
for slot in ("L01", "L02"):
    st = states(slot)
    tr = trades(slot)
    print(f"\n{slot}: períodos em caixa (entre a venda e a recompra) e movimento do ativo no período")
    for i in range(1, len(tr) - 1, 2):
        out, back = tr.iloc[i], tr.iloc[i + 1]
        days = lbh.loc[out.date:back.date].iloc[1:-1]
        print(f"   vendeu {out.date.date()} @{out.price:.4f} → recomprou {back.date.date()} @{back.price:.4f}"
              f" ({back.price / out.price - 1:+.2%}); B&H nos {len(days)} pregões inteiros em caixa: {math.expm1(days.sum()):+.2%}")
    last = tr.iloc[-1]
    days = lbh.loc[last.date:].iloc[1:]
    print(f"   vendeu {last.date.date()} @{last.price:.4f} → fim da janela; B&H nos {len(days)} pregões: {math.expm1(days.sum()):+.2%}")

# ── 3. Camadas: técnico, consenso, risco, PM, ordens ───────────────
section("3. Camadas de decisão")
for slot in SLOTS:
    d = dec[slot].values()
    risk = collections.Counter((x["risk_source"], x["risk_rule"]) for x in d if x["risk_verdict"] == "VETADO")
    pm_calls = [c for c in calls[slot] if c["stage"] == "portfolio_manager"]
    followed = sum(c["validated_response"]["decision"] == json.loads(c["user_prompt"])["technical_signal"]["signal"] for c in pm_calls)
    rm_calls = [c for c in calls[slot] if c["stage"] == "risk_manager"]
    print(f"{slot}: final_cause {dict(collections.Counter(x['final_cause'] for x in d))}")
    print(f"     vetos {dict(risk)}; Risk LLM {len(rm_calls)} chamadas, aprovou"
          f" {sum(c['validated_response']['verdict'] == 'APROVADO' for c in rm_calls)}; PM {len(pm_calls)} chamadas,"
          f" seguiu o sinal em {followed}; ordens {len(trades(slot))}")
    assert set(risk) == {("HARD_RULE", "CONCENTRATION")} and followed == len(pm_calls)
    assert all(x["final_cause"] == "BUY_AT_TARGET_NOOP" for x in d if x["risk_verdict"] == "VETADO")
    assert not any(x["final_cause"] == "TECH_NO_MAJORITY" for x in d)
regime = collections.Counter()
for day, f in features.items():
    key = ("close>SMA50" if f["sma50_gap"] > 0 else "close<SMA50") + (" MACD>sinal" if f["macd_ratio"] > f["macd_signal_ratio"] else " MACD<sinal")
    regime[(key, dec["L01"][day]["technical_outcome"])] += 1
print("L01, consenso por estado (posição vs SMA50, MACD vs sinal):")
for key in sorted({k for k, _ in regime}):
    print(f"   {key}: {({o: regime[(key, o)] for o in ('COMPRA', 'VENDA', 'MANTER') if regime[(key, o)]})}")
for slot in SLOTS:
    entries = [features[str(prev[t].date())]["sma50_gap"] for t in trades(slot).query("type == 'BUY'").date]
    exits = [features[str(prev[t].date())]["sma50_gap"] for t in trades(slot).query("type == 'SELL'").date]
    assert min(entries) > 0 and max(exits) < 0
print("toda compra decidida com close > SMA50 e toda venda com close < SMA50 (3 runs)")

# ── 4. L02 × L03 ────────────────────────────────────────────────────
section("4. L02 e L03: mesmas perguntas, respostas independentes, divergências neutras")
for f in ("equity.csv", "trades.csv"):
    assert (run("L02") / f).read_bytes() == (run("L03") / f).read_bytes()
ids = [c["provider_response_id"] for s in SLOTS for c in calls[s]]
assert len(ids) == len(set(ids)) == 3963
journals = {s: jsonl(run(s) / "provider_journal.jsonl") for s in SLOTS}
envelopes = {s: {r["raw_sha256"] for r in journals[s]} for s in SLOTS}
assert not (envelopes["L01"] & envelopes["L02"]) and not (envelopes["L02"] & envelopes["L03"]) and not (envelopes["L01"] & envelopes["L03"])
windows = {s: (min(c["started_at"] for c in calls[s]), max(c["started_at"] for c in calls[s])) for s in SLOTS}
assert windows["L01"][1] < windows["L02"][0] and windows["L02"][1] < windows["L03"][0]
print("responseId distintos 3963/3963; envelopes HTTP sem repetição entre runs; janelas (UTC):", windows)
ta = {s: {(c["decision_session"], c["analyst_id"]): c for c in calls[s] if c["stage"] == "technical_analyst"} for s in SLOTS}
for a, b in (("L01", "L02"), ("L01", "L03"), ("L02", "L03")):
    assert all(ta[a][k]["identity_digest"] == ta[b][k]["identity_digest"] for k in ta[a])
    same = sum(ta[a][k]["validated_response"]["signal"] == ta[b][k]["validated_response"]["signal"] for k in ta[a])
    print(f"{a}×{b}: 1235/1235 requisições técnicas idênticas; mesmo voto em {same}/1235")


def effect(x):
    if x["final_cause"] == "ACTION_BUY" and x["observed_weight"] < 1:
        return "BUY"
    return "SELL" if x["final_cause"] == "ACTION_SELL" and x["observed_weight"] > 0 else "NONE"


for a, b in (("L02", "L03"), ("L01", "L02")):
    diff = [k for k in dec[a] if dec[a][k]["technical_outcome"] != dec[b][k]["technical_outcome"]]
    moved = [k for k in dec[a] if effect(dec[a][k]) != effect(dec[b][k])]
    print(f"{a}×{b}: votos diferem em {sum(dec[a][k]['vote_counts'] != dec[b][k]['vote_counts'] for k in dec[a])} sessões;"
          f" resultado técnico em {len(diff)}; efeito na posição em {moved}")
    for k in diff:
        print(f"   {k} {a} {dec[a][k]['vote_counts']} {dec[a][k]['final_cause']} w={dec[a][k]['observed_weight']}"
              f" | {b} {dec[b][k]['vote_counts']} {dec[b][k]['final_cause']} w={dec[b][k]['observed_weight']}")
    assert (a, b) != ("L02", "L03") or not moved

# ── 5. risk_max_drawdown = 0,25 ─────────────────────────────────────
section("5. Drawdown: limite de veto vs drawdown realizado")
for slot in SLOTS:
    eq = equity(slot)
    dd = 1 - eq / eq.cummax()
    sent = []
    for c in calls[slot]:
        if c["stage"] != "technical_analyst":
            p = json.loads(c["user_prompt"])
            metrics = p["risk_metrics"] if c["stage"] == "risk_manager" else p["risk_verdict"]["risk_metrics"]
            sent.append((c["decision_session"], metrics["current_drawdown"]))
    assert all(v == canon(dd[pd.Timestamp(day)]) for day, v in sent)
    buys_over = [k for k, x in dec[slot].items() if x["technical_outcome"] == "COMPRA" and canon(dd[pd.Timestamp(k)]) > 0.25]
    assert not buys_over
    worst_buy = max(canon(dd[pd.Timestamp(k)]) for k, x in dec[slot].items() if x["final_cause"] == "ACTION_BUY")
    after = collections.Counter(x["final_cause"] for k, x in dec[slot].items() if k > "2025-08-08" and dd[pd.Timestamp(k)] > 0.25)
    t = dd.idxmax()
    print(f"{slot}: MDD {dd.max():.4%} em {t.date()} (fech. {close[t]:.4f} vs {close[prev[t]]:.4f}:"
          f" {close[t] / close[prev[t]] - 1:+.2%} no pregão, 100% comprado); maior DD numa COMPRA executada {worst_buy};"
          f" COMPRA com DD>0,25: nenhuma; após 2025-08-08 com DD>0,25: {dict(after)}; {len(sent)} drawdowns enviados = recalculados")

# ── 6. Atribuição exata H2 vs B&H e Bollinger ───────────────────────
section("6. Atribuição em log-retorno (soma exata) H2 − B&H")
for slot in ("L01", "L02"):
    lh = np.log(equity(slot) / equity(slot).shift(1)).dropna()
    st = states(slot).loc[lh.index]
    d = lh - lbh
    assert d[st == "long"].abs().max() < 1e-12
    parts = {k: (d[st == k].sum(), lbh[st == k].sum(), int((st == k).sum())) for k in ("long", "cash", "entry", "exit")}
    print(f"{slot}: total {d.sum():+.4f} = " + ", ".join(f"{k} {v[0]:+.4f} ({v[2]} dias; B&H {v[1]:+.4f})" for k, v in parts.items()))
lboll = np.log(equity("bollinger_state_h2_proposed") / equity("bollinger_state_h2_proposed").shift(1)).dropna()
for slot in ("L01", "L02"):
    lh = np.log(equity(slot) / equity(slot).shift(1)).dropna()
    fold = {"entry": "long", "exit": "cash"}
    frame = pd.DataFrame({"h2": states(slot).loc[lh.index].replace(fold),
                          "boll": states("bollinger_state_h2_proposed").loc[lh.index].replace(fold),
                          "H2": lh, "BOLL": lboll, "BH": lbh})
    print(f"{slot} × Bollinger, log-retornos por exposição conjunta:")
    print(frame.groupby(["h2", "boll"]).agg(dias=("H2", "size"), H2=("H2", "sum"), BOLL=("BOLL", "sum"), BH=("BH", "sum")).round(4).to_string())
h2_sells = dict(zip(trades("L01").query("type == 'SELL'").date, trades("L01").query("type == 'SELL'").price))
boll = trades("bollinger_state_h2_proposed")
print("Bollinger:", [f"{d.date()} {t} {p:.4f}{' (= venda H2 na mesma abertura)' if t == 'BUY' and h2_sells.get(d) == p else ''}"
                     for d, t, p in zip(boll.date, boll.type, boll.price)])

# ── 7. Custos: 9 N/A ────────────────────────────────────────────────
section("7. Replay de custos: reconstrução dos prompts divergentes")
closure = json.loads((VAL / "cost_closure.json").read_text(encoding="utf-8"))["report"]
recorded = calls["L01"][67]
assert all(calls[s][67]["identity_digest"] == recorded["identity_digest"] for s in SLOTS)
for spread in (0, 10, 20):
    eq = equity("buy_and_hold", spread).loc[:"2024-09-18"]
    payload = json.loads(recorded["user_prompt"])
    payload["risk_verdict"]["risk_metrics"]["current_drawdown"] = canon((eq.max() - eq.iloc[-1]) / eq.max())
    rebuilt = sha(json.dumps(payload, ensure_ascii=False, sort_keys=True).encode())
    for item in closure[str(spread)]["individual"]:
        assert item["affected_call"] == recorded["call_id"] and item["consumed_calls"] == 67
        assert item["reason"].endswith(f"replayed='{rebuilt}'") and "; " not in item["reason"]
    print(f"{spread:2d} bps: current_drawdown {payload['risk_verdict']['risk_metrics']['current_drawdown']}"
          f" (5 bps: 0.068822) → sha {rebuilt[:16]}… = replayed nos 3 runs")
assert all(x["status"] == "BASELINE_REUSED" for x in closure["5"]["individual"])
uri = (VAL / "evaluation.sqlite").as_uri() + "?mode=ro&immutable=1"
with contextlib.closing(sqlite3.connect(uri, uri=True)) as db:
    states_db = collections.Counter(r[0] for r in db.execute("SELECT state FROM dispositions"))
print("disposições:", dict(states_db))

# ── 8. summary.json × arquivos originais ────────────────────────────
section("8. Métricas reportadas × recálculo a partir de equity/trades")
summary = json.loads((VAL / "summary.json").read_text(encoding="utf-8"))
reported = [(x["slot"], 5, x) for x in summary["individual"]] + [(x["kind"], 5, x) for x in summary["benchmarks"]]
for spread, block in closure.items():
    reported += [(x["kind"].replace(f"-cost-{spread}", ""), int(spread), x) for x in block["benchmarks"]]
    reported += [(x["slot"], int(spread), x) for x in block["individual"] if x.get("metrics")]
worst = 0.0
for name, spread, item in reported:
    eq = equity(name, spread)
    manifest = json.loads((run(name, spread) / "manifest.json").read_text(encoding="utf-8"))
    assert performance_metrics(eq) == item["metrics"] == manifest["metrics"]
    assert manifest["final_equity"] == eq.iloc[-1] and manifest["trade_count"] == len(trades(name, spread))
    tr = trades(name, spread)
    notional = math.fsum(abs(tr.price * tr.quantity))
    for key, value in (("executed_notional", notional), ("turnover", notional / 1e5), ("total_cost", math.fsum(tr.cost)),
                       ("executed_orders", len(tr))):
        worst = max(worst, abs(item["secondary"][key] - value))
r = {k: equity(k).pct_change().dropna() for k in ("buy_and_hold", *SLOTS)}
sharpe = {k: v.mean() / v.std(ddof=1) * math.sqrt(252) for k, v in r.items()}
stats = summary["statistics"]
assert stats["sharpe_individual"] == [sharpe[s] for s in SLOTS] and stats["sharpe_buy_and_hold"] == sharpe["buy_and_hold"]
assert stats["delta"] == float(np.mean([sharpe[s] for s in SLOTS]) - sharpe["buy_and_hold"])
assert checkpoint["statistics"] == stats
print(f"{len(reported)} blocos de métricas idênticos bit a bit (summary, cost_closure, manifest, recálculo);"
      f" secundárias |Δ| ≤ {worst:.1e}; estatísticas idênticas")
print("rótulo amendment_status em summary.json:", summary["amendment_status"])
retried = [(s, r["sequence"], [a["state"] for a in r["attempts"]]) for s in SLOTS for r in journals[s] if len(r["attempts"]) > 1]
print("journal com >1 tentativa:", retried, "| attempt_count no llm_calls.jsonl:", [calls[s][q]["attempt_count"] for s, q, _ in retried])
assert all(r["request_identity"] == c["identity_digest"] and r["record"]["validated_response"] == c["validated_response"]
           for s in SLOTS for r, c in zip(journals[s], calls[s]))
print("\nDIAGNÓSTICO: todos os asserts passaram")
