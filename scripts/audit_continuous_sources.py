"""Read-only coverage audit, retaining the raw archives used by this replay."""
import json
from pathlib import Path

import replay_multiasset as r
from continuous_replay_data import ROOT, SOURCE


def audit():
    platform = SOURCE / "data/platform"
    r.market.ROOT = platform / "market-base-v1"
    r.stock.ROOT = platform / "stock-history-v1"
    coverage = {}
    for ticker in r.radar.EXAMPLES:
        rows = r.market.merged(ticker)
        yahoo = r.stock.load(ticker)
        coverage[ticker] = {"b3_raw": {"start": rows[0]["date"], "end": rows[-1]["date"], "bars": len(rows)}, "yahoo_snapshot": {"start": yahoo["rows"][0]["date"], "end": yahoo["rows"][-1]["date"], "bars": len(yahoo["rows"]), **{k: yahoo[k] for k in ("through", "fetched_at", "raw_sha256", "requested_period")}}}
    archives = []
    for item in r.market.acquired():
        if item.get("year") not in (2025, 2026):
            continue
        path = SOURCE / "data/raw/cotahist" / item["file_name"].split("+")[0]
        present = path.exists()
        match = present and r.b.sha_file(path) == item["raw_sha256"]
        if match:
            r.radar.write(ROOT / "source/raw" / (item["raw_sha256"] + ".zip"), path.read_bytes(), immutable=True)
        archives.append({"file": item["file_name"], "raw_sha256": item["raw_sha256"], "cached_original_present": present, "cached_original_matches": match, "normalized_through": item["through"]})
    value = {"main_checkout": str(SOURCE), "coverage_before_completion": coverage, "annual_raw_archives": archives, "normalized_b3_storage": "data/platform/market-base-v1/b3/*.json (sealed records)", "yahoo_storage": "data/platform/stock-history-v1/<ticker>/<sha>.csv and sealed normalized JSON", "campaign_data_audit": r.checked(ROOT / "data_audit.json"), "replay_bundle": {t: {"start": v["rows"][0]["date"], "end": v["rows"][-1]["date"], "bars": len(v["rows"])} for t, v in r.checked(ROOT / "inputs/market.json")["assets"].items()}}
    r.save(ROOT / "coverage_audit_v2.json", value)
    return value


if __name__ == "__main__":
    print(json.dumps(audit(), indent=2))
