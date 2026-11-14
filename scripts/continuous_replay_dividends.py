"""Campaign-only repair: distinct B3 components may share ex/payment/type dates.

Keep entitlement math and the immutable book unchanged. Give each raw-rate
component its own command identity; recognize already booked legacy components
by their exact payload, without deleting or correcting any earlier event.
"""
from contextlib import closing


def install(dividends, manual, RecoveryStop):
    b = manual.b

    def book_received(today, wallets=None):
        if wallets is None:
            wallets = [w for w in manual.get({})["wallets"] if w.get("strategy") not in manual.RULE_STRATEGIES]
        out = {"booked": 0, "already": 0, "refused": []}
        with closing(manual.connect(write=True)) as conn, conn:
            for original in wallets:
                history = manual.events(conn, original["id"])
                wallet = manual.replay(history)
                legacy = [x for x in wallet["dividends"] if not (x.get("source") or {}).get("component_identity")]
                seen = set()
                for e in dividends.entitlements(wallet, today):
                    if e["state"] != "RECEBIDO":
                        continue
                    identity = b.digest([e[k] for k in ("ticker", "kind", "data_com", "payment_date", "label", "value_per_share")])
                    if identity in seen:
                        raise RecoveryStop("duplicate_indistinguishable_b3_dividend_component")
                    seen.add(identity)
                    fields = ("ticker", "kind", "data_com", "payment_date", "quantity", "gross", "net")
                    req = manual.request({"kind": "DIVIDEND", "wallet": wallet["id"], "dividend": {k: e[k] for k in fields}})
                    cid = "dividend-component-" + b.digest([wallet["id"], identity])
                    stored = manual.canonical(req)
                    prior = conn.execute("SELECT request FROM events WHERE command=?", (cid,)).fetchone()
                    if prior:
                        if prior[0] != stored:
                            raise RecoveryStop("dividend_component_payload_changed")
                        out["already"] += 1
                        continue
                    match = next((x for x in legacy if all(x[k] == req["dividend"][k] for k in fields)), None)
                    if match is not None:
                        legacy.remove(match)
                        out["already"] += 1
                        continue
                    snap = dividends.snapshot(e["ticker"])
                    source = {"snapshot_sha256": snap["sha256"], "url": snap["url"], "component_identity": identity, "value_per_share": e["value_per_share"], "label": e["label"]}
                    event = manual.append(conn, req, cid, stored, wallet["id"], history[-1]["sha256"], source)
                    history.append(event)
                    out["booked"] += 1
                manual.replay(history)
        return out

    dividends.book_received = book_received
