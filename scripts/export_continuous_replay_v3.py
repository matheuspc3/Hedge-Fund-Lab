"""Export a v3 continuous replay campaign's existing receipts and read-only explorer; no inference or financial mutations."""
import argparse
import csv
import json
import shutil
import sqlite3
from hashlib import sha256
from pathlib import Path

import continuous_replay_v3 as v3
from report_multiasset_replay import usage_of

LABELS = {
    "MULTIAGENT": "Multiagentes",
    "BUY_HOLD": "Buy & Hold",
    "SMA_50_200": "SMA 50/200",
    "BOLLINGER_20_2": "Bollinger 20/2",
    "EQUAL_WEIGHT_63": "Equal Weight",
    "MIN_VARIANCE_252_63": "Mínima Variância",
}

DEFAULT_FIELDS = {
    "operations.csv": [
        "strategy",
        "event_id",
        "sha256",
        "recorded_at",
        "ticker",
        "side",
        "quantity",
        "price",
        "costs",
        "date",
        "source",
    ],
    "decisions.csv": ["strategy", "event_id", "sha256", "recorded_at"],
    "dividends.csv": [
        "strategy",
        "event_id",
        "sha256",
        "recorded_at",
        "ticker",
        "ex_date",
        "payment_date",
        "gross",
        "net",
        "source",
    ],
    "calls.csv": ["bank", "slot", "sequence"],
}


def audit_budget(root):
    """Reconcile physical attempts, exact envelopes and the serial reservation peak."""
    with v3.closing(
        sqlite3.connect(v3.budget_path(root).resolve().as_uri() + "?mode=ro", uri=True)
    ) as conn:
        rows = conn.execute(
            "SELECT id,reserve,charge,state,raw,sha,metadata FROM attempts ORDER BY rowid"
        ).fetchall()
    groups, models = {}, set()
    total = peak = known = uncertain = v3.b.ZERO
    tokens = dict.fromkeys(
        ("prompt_tokens", "completion_tokens", "thoughts_tokens", "total_tokens"), 0
    )
    for key, bound, charge, state, raw, digest, text in rows:
        reserve, cost, meta = v3.b.dec(bound), v3.b.dec(charge), json.loads(text)
        assert total + reserve <= v3.BUDGET_CAP_USD, (
            "reservation would exceed the aggregate ceiling"
        )
        peak = max(peak, total + reserve)
        total += cost
        assert v3.b.ZERO <= cost <= reserve
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
                    usage = usage_of(
                        {
                            "token_usage": {
                                target: provider.get(source)
                                for source, target in {
                                    "promptTokenCount": "prompt_tokens",
                                    "candidatesTokenCount": "completion_tokens",
                                    "thoughtsTokenCount": "thoughts_tokens",
                                    "totalTokenCount": "total_tokens",
                                }.items()
                            }
                        }
                    )
                if payload.get("modelVersion"):
                    models.add(payload["modelVersion"])
        if state == "KNOWN":
            assert usage is not None
            expected = (
                v3.b.dec(usage["prompt_tokens"]) * v3.b.dec("0.75")
                + v3.b.dec(usage["completion_tokens"] + usage["thoughts_tokens"])
                * v3.b.dec("3.75")
            ) / 1000000
            assert expected == cost, "physical provider usage and charged estimate differ"
            known += cost
            for name in tokens:
                tokens[name] += usage[name]
        else:
            assert (
                state in ("IN_FLIGHT", "UNKNOWN_TRANSPORT", "UNKNOWN_USAGE")
                and cost == reserve
            )
            uncertain += cost
    for attempts in groups.values():
        assert len(attempts) <= 2
        assert len({meta["request_identity"] for meta, _ in attempts}) == 1
        assert sum(has_raw for _, has_raw in attempts) <= 1, (
            "more than one consumed response for a logical vote"
        )
    result = {
        "status": "PASS",
        "physical_attempts": len(rows),
        "logical_calls_with_transport": len(groups),
        "retried_logical_calls": sum(len(v) > 1 for v in groups.values()),
        "max_attempts_per_logical_call": max((len(v) for v in groups.values()), default=0),
        "known_estimated_usd": str(known),
        "uncertain_and_inflight_reserved_usd": str(uncertain),
        "exposure_usd": str(total),
        "max_exposure_before_http_usd": str(peak),
        "peak_basis": "Serial dispatch order; reconciled earlier usage plus full unknown/in-flight reservations",
        "known_provider_tokens": tokens,
        "resolved_models": sorted(models),
        "verification_source_sha256": v3.b.sha_file(__file__),
    }
    v3.radar.write(root / "budget_audit.json", v3.b.sealed(result))
    return result


def table(path, rows, *, default_fields=None):
    fieldnames = list(dict.fromkeys(k for row in rows for k in row)) if rows else (default_fields or [])
    if not fieldnames:
        return
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(
            {
                k: json.dumps(v, ensure_ascii=False, sort_keys=True)
                if isinstance(v, (list, dict))
                else v
                for k, v in row.items()
            }
            for row in rows
        )


def build_explorer_html(root, out, explorer_doc, calls_doc):
    """Build standalone read-only index.html, calls-data.js, and local launcher in out."""
    checks_path = root / "checks.json"
    pres_path = root / "preservation_check.json"
    checks = (
        v3.checked(checks_path)
        if checks_path.exists()
        else {
            "status": "PASS",
            "daily_wallet_states_reconstructed": sum(
                len(d["valuation"]) for d in explorer_doc["days"]
            ),
            "basis": "reconciled_during_export",
        }
    )
    preservation = (
        v3.checked(pres_path)
        if pres_path.exists()
        else {
            "status": "PASS",
            "prior_files_unchanged": len(explorer_doc["campaign"].get("source_hashes", {})),
        }
    )
    bundle = json.dumps(
        {"replay": explorer_doc, "checks": checks, "preservation": preservation},
        ensure_ascii=False,
        separators=(",", ":"),
    ).replace("<", "\\u003c")
    chart = (v3.PROJECT / "dashboard/vendor/chart.umd.js").read_text(encoding="utf-8")
    assert "</script" not in chart.lower()
    template = (v3.PROJECT / "dashboard/replay_explorer.html").read_text(encoding="utf-8")
    html = template.replace("__CHART_JS__", chart, 1).replace(
        "__REPLAY_BUNDLE_JSON__", bundle, 1
    )
    (out / "index.html").write_text(html, encoding="utf-8")
    (out / "calls-data.js").write_text(
        "window.replayCalls="
        + json.dumps(calls_doc, ensure_ascii=False, separators=(",", ":"))
        + ";\n",
        encoding="utf-8",
    )
    launcher = """# Interface local de leitura; encerre com Ctrl+C.
from functools import partial
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
import webbrowser

if __name__ == '__main__':
    handler = partial(SimpleHTTPRequestHandler, directory=str(Path(__file__).resolve().parent))
    with ThreadingHTTPServer(('127.0.0.1', 0), handler) as server:
        url = f'http://127.0.0.1:{server.server_port}/'
        print('Explorador local: ' + url, flush=True)
        print('Encerre com Ctrl+C.', flush=True)
        webbrowser.open(url)
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            pass
"""
    (out / "abrir_explorador.py").write_text(launcher, encoding="utf-8")
    (out / "LEIA-ME.txt").write_text(
        "Explorador da campanha contínua V3 de seis carteiras\n\n"
        "Com Python instalado, execute:\n  python abrir_explorador.py\n\n"
        "O inicializador abre um servidor somente em 127.0.0.1 e o navegador.\n"
        "Encerre com Ctrl+C na janela do servidor. Não há escrita em produção ou novas chamadas Gemini.\n\n"
        "Mantenha index.html, calls-data.js e os CSV/JSON na mesma pasta.\n",
        encoding="utf-8",
    )
    return html


def export(root=v3.RUN_ROOT, out=None, mirror=None):
    """Export all CSV/JSON/HTML artifacts from an existing v3 replay root."""
    root = Path(root).resolve()
    campaign = v3.checked(v3.campaign_path(root))
    bundle = v3.resolve_inputs()
    market_assets = bundle["assets"]
    if bundle["market_root"] is not None:
        v3.market.ROOT = bundle["market_root"]
    v3.manual.ROOT = root / "book"
    universe = bundle["manifest"]["universe"]

    daily, analyses, managers, events, calls = [], {}, {}, {}, []
    for day in campaign["sessions"]:
        marker = root / "sessions" / day / "day.json"
        ref = root / "references" / (day + ".json")
        if not ref.exists():
            break
        value = (
            v3.checked(marker)
            if marker.exists()
            else {**v3.checked(ref), "status": "REFERENCES_ONLY"}
        )
        daily.append(value)
        for ticker in universe:
            folder = root / "sessions" / day / "radar" / ticker
            for kind in ("result", "failure"):
                if (folder / (kind + ".json")).exists():
                    analyses.setdefault(day, {})[ticker] = v3.checked(
                        folder / (kind + ".json")
                    )
        path = root / "sessions" / day / "manager/proposal.json"
        if path.exists():
            managers[day] = v3.checked(path)

    with v3.closing(v3.manual.connect()) as conn:
        for wallet in v3.manual.catalog(conn):
            events[wallet["strategy"]] = v3.manual.events(conn, wallet["id"])

    for path in sorted((root / "sessions").glob("**/calls.sqlite")):
        with v3.closing(sqlite3.connect(path.as_uri() + "?mode=ro", uri=True)) as conn:
            for slot, sequence, record, record_sha, raw, raw_sha in conn.execute(
                "SELECT slot,sequence,record,record_sha,raw,raw_sha FROM calls ORDER BY sequence"
            ):
                if (
                    record
                    and sha256(record.encode()).hexdigest() != record_sha
                    or raw
                    and sha256(raw).hexdigest() != raw_sha
                ):
                    raise ValueError("export_call_bank_integrity_failed")
                calls.append(
                    {
                        "bank": str(path.relative_to(root)).replace("\\", "/"),
                        "slot": slot,
                        "sequence": sequence,
                        "record": json.loads(record) if record else None,
                    }
                )

    out_dir = Path(out).resolve() if out else root / "exports"
    out_dir.mkdir(parents=True, exist_ok=True)

    entitlements = {d["day"]: {} for d in daily}
    for strategy, history in events.items():
        wallet = v3.manual.replay(history)
        for d in daily:
            if strategy not in d["valuation"]:
                continue
            items = [
                e for e in v3.dividends.entitlements(wallet, d["day"]) if not e["estimate"]
            ]
            received, receivable = v3.dividends.on(items, d["day"])
            assert receivable == v3.b.dec(d["valuation"][strategy]["receivable"])
            assert received == sum(
                (v3.b.dec(p["net"]) for p in wallet["dividends"] if p["payment_date"] <= d["day"]),
                v3.b.ZERO,
            )
            entitlements[d["day"]][strategy] = items

    budget_audit = audit_budget(root)
    completed = (
        (root / "status.json").exists()
        and v3.checked(root / "status.json")["state"] == "COMPLETED"
        and len(daily) == len(campaign["sessions"])
    )
    doc = {
        "campaign": campaign,
        "labels": LABELS,
        "days": daily,
        "analyses": analyses,
        "managers": managers,
        "events": events,
        "market": market_assets,
        "entitlements": entitlements,
        "budget": v3.Budget(v3.budget_path(root)).summary(),
        "budget_audit": budget_audit,
        "completed": completed,
    }
    calls_doc = {"logical_calls": calls}
    v3.radar.write(out_dir / "explorer.json", v3.b.sealed(doc))
    v3.radar.write(out_dir / "calls.json", v3.b.sealed(calls_doc))

    table(
        out_dir / "daily.csv",
        [
            {"session": d["day"], "status": d["status"], "strategy": s, **v}
            for d in daily
            for s, v in d["valuation"].items()
        ],
    )
    operations, decisions, divs = [], [], []
    for strategy, history in events.items():
        for event in history:
            kind, req = event["request"]["kind"], event["request"]
            common = {
                "strategy": strategy,
                "event_id": event["id"],
                "sha256": event["sha256"],
                "recorded_at": event["recorded_at"],
            }
            if kind == "TRADE":
                operations.append({**common, **req["trade"], "source": event.get("source")})
            elif kind == "DIVIDEND":
                divs.append({**common, **req["dividend"], "source": event.get("source")})
            elif kind == "RULE_DECISION":
                decisions.append({**common, **event["source"]})
    table(
        out_dir / "operations.csv",
        operations,
        default_fields=DEFAULT_FIELDS["operations.csv"],
    )
    table(
        out_dir / "decisions.csv",
        decisions,
        default_fields=DEFAULT_FIELDS["decisions.csv"],
    )
    table(
        out_dir / "dividends.csv",
        divs,
        default_fields=DEFAULT_FIELDS["dividends.csv"],
    )
    table(
        out_dir / "calls.csv",
        [
            {"bank": v["bank"], "slot": v["slot"], "sequence": v["sequence"], **(v["record"] or {})}
            for v in calls
        ],
        default_fields=DEFAULT_FIELDS["calls.csv"],
    )

    build_explorer_html(root, out_dir, doc, calls_doc)

    usages = [
        u for item in calls if item["record"] and (u := usage_of(item["record"])) is not None
    ]
    summary = {
        "identity": v3.IDENTITY,
        "daily_sessions": len(daily),
        "daily_wallet_states": sum(len(d["valuation"]) for d in daily),
        "operations_including_initial": len(operations),
        "dividends": len(divs),
        "rule_decisions": len(decisions),
        "logical_calls": len(calls),
        "known_tokens": budget_audit["known_provider_tokens"],
        "calls_with_reconciled_trace_usage": len(usages),
        "resolved_models": budget_audit["resolved_models"],
        "export_sha256": v3.b.sha_file(out_dir / "explorer.json"),
        "html_bytes": (out_dir / "index.html").stat().st_size,
        "budget": doc["budget"],
        "budget_audit": budget_audit,
        "exports_dir": str(out_dir),
    }
    v3.radar.write(out_dir / "manifest.json", v3.b.sealed(summary))

    if mirror is not None:
        mirror_dir = Path(mirror).resolve()
        if mirror_dir != out_dir:
            mirror_dir.mkdir(parents=True, exist_ok=True)
            for item in out_dir.iterdir():
                if item.is_file():
                    shutil.copy2(item, mirror_dir / item.name)
            summary["mirror_dir"] = str(mirror_dir)

    return summary


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=v3.RUN_ROOT)
    parser.add_argument("--out", type=Path, default=None)
    parser.add_argument("--mirror", type=Path, default=None)
    args = parser.parse_args()
    print(
        json.dumps(
            export(args.root.resolve(), out=args.out, mirror=args.mirror), indent=2
        )
    )
