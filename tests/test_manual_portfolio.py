"""APP-01/02 check: python -B tests/test_manual_portfolio.py [--browser]."""

import http.client
import json
import os
import sqlite3
import subprocess
import sys
import tempfile
import threading
import unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(PROJECT / "dashboard"), str(PROJECT / "scripts"), str(PROJECT)]
import server  # noqa: E402

m = server.manual_portfolio_api


def operation(
    wallet,
    side="BUY",
    quantity="10",
    price="20.00",
    costs="2.00",
    economic_date="2020-01-02",
):
    return {
        "kind": "TRADE",
        "wallet": wallet,
        "trade": {
            "ticker": "PETR4",
            "side": side,
            "quantity": quantity,
            "price": price,
            "costs": costs,
            "economic_date": economic_date,
        },
    }


def confirmation(r, cid, token=None):
    return {"request": r, "command_id": cid, "preview_token": token, "confirm": True}


class ManualCheck(unittest.TestCase):
    def setUp(self):
        base = PROJECT / "data/cache"
        base.mkdir(parents=True, exist_ok=True)
        self.temp = tempfile.TemporaryDirectory(prefix="hfl-personal-", dir=base)
        self.old = m.ROOT
        m.ROOT = Path(self.temp.name)

    def tearDown(self):
        m.ROOT = self.old
        self.temp.cleanup()

    def create(self, name="Pessoal", nature="EXTERNAL", capital="1000.00"):
        r = {
            "kind": "CREATE",
            "name": name,
            "nature": nature,
            "capital": capital,
            "start_date": "2020-01-01",
        }
        return m.post("confirm", confirmation(r, name))["wallet"]

    def record(self, r, cid):
        p = m.post("preview", {"request": r})
        payload = confirmation(r, cid, p["preview_token"])
        return m.post("confirm", payload), payload

    def test_full_accounting_history_correction_idempotency_and_isolation(self):
        self.assertEqual(m.get({})["wallets"], [])
        self.assertFalse(m.path().exists())  # GET never initializes a store.
        w = self.create()
        bought, payload = self.record(operation(w["id"]), "buy")
        b = bought["wallet"]
        self.assertEqual(
            (b["cash"], b["positions"][0]["average_cost"]), ("798.00", "20.20000000")
        )
        self.assertIsNone(b["equity"])
        self.assertIsNone(b["return_pct"])
        self.assertEqual(b["daily_history"], [])
        self.assertEqual(m.post("confirm", payload)["event_id"], bought["event_id"])
        self.assertEqual(len(m.get({})["wallets"][0]["audit"]), 1)
        sold, _ = self.record(
            operation(w["id"], "SELL", "4", "30.00", "1.00", "2020-01-04"), "sell"
        )
        s = sold["wallet"]
        self.assertEqual(
            (
                s["cash"],
                s["positions"][0]["quantity"],
                s["positions"][0]["average_cost"],
                s["realized_pnl"],
            ),
            ("917.00", "6", "20.20000000", "38.20"),
        )
        historical, _ = self.record(
            operation(
                w["id"],
                quantity="10",
                price="10.00",
                costs="0",
                economic_date="2020-01-01",
            ),
            "old",
        )
        h = historical["wallet"]
        self.assertEqual(
            (h["cash"], h["positions"][0]["quantity"], h["positions"][0]["average_cost"]),
            ("817.00", "16", "15.10000000"),
        )
        self.assertTrue(
            all(t["recorded_at"][:10] > t["economic_date"] for t in h["trades"])
        )
        r = {
            "kind": "CORRECTION",
            "wallet": w["id"],
            "target": bought["event_id"],
            "reason": "Preço digitado incorretamente",
            "trade": {**operation(w["id"])["trade"], "price": "22.00"},
        }
        revised, _ = self.record(r, "correct")
        self.assertEqual(revised["wallet"]["cash"], "797.00")
        self.assertEqual(revised["wallet"]["audit"][0]["trade"]["price"], "20.00")
        self.assertEqual(revised["wallet"]["audit"][-1]["target"], bought["event_id"])
        self.assertEqual(len(revised["wallet"]["audit"]), 4)
        self.record(
            {
                "kind": "CORRECTION",
                "wallet": w["id"],
                "target": historical["event_id"],
                "reason": "Anular duplicado",
                "trade": None,
            },
            "void",
        )
        other = self.create("Simulada", "SIMULATION", "100000.00")
        self.assertEqual(other["cash"], "100000.00")
        self.assertEqual(other["trades"], [])
        self.assertIsNone(other["comparison_group"])
        self.assertEqual(m.get({})["pilot"]["status"], "PENDING")

    def test_exclude_unused_wallet_preserves_history_and_rejects_new_trades(self):
        w = self.create()
        r = {"kind": "ARCHIVE", "wallet": w["id"], "reason": "Cadastro equivocado"}
        archived, payload = self.record(r, "archive")
        self.assertTrue(archived["wallet"]["archived"])
        self.assertEqual(m.get({})["wallets"], [])
        self.assertTrue(m.post("confirm", payload)["replayed"])
        with self.assertRaises(m.Invalid):
            m.post("preview", {"request": operation(w["id"])})
        from contextlib import closing

        with closing(m.connect()) as conn:
            history = m.events(conn, w["id"])
            self.assertEqual(len(history), 2)
            self.assertEqual(history[0]["request"]["nature"], "EXTERNAL")
            self.assertEqual(history[-1]["request"]["reason"], "Cadastro equivocado")
        used = self.create("Em uso")
        self.record(operation(used["id"]), "buy")
        with self.assertRaises(m.Invalid):
            m.post("preview", {"request": {**r, "wallet": used["id"]}})

    def test_common_initialization_metadata_does_not_activate_agents(self):
        r = {
            "kind": "CREATE",
            "name": "Buy & Hold",
            "nature": "SIMULATION",
            "capital": "100000.00",
            "start_date": "2020-01-01",
            "strategy": "BUY_HOLD",
            "comparison_group": "manual-initial",
            "initialization_note": "Preço de referência declarado; não é fill prospectivo.",
        }
        w = m.post("confirm", confirmation(r, "base"))["wallet"]
        self.assertEqual(w["comparison_group"], "manual-initial")
        self.assertEqual(w["strategy"], "BUY_HOLD")
        self.assertEqual(w["initialization_note"], r["initialization_note"])
        self.assertEqual(w["trades"], [])
        self.assertEqual(m.get({})["pilot"]["status"], "PENDING")
        with self.assertRaises(m.Invalid):
            m.request({**r, "nature": "EXTERNAL"})
        with self.assertRaises(m.Invalid):
            m.request({**r, "strategy": "AUTO_EXECUTE"})

    def test_guards_replay_stale_preview_and_rollback(self):
        w = self.create()
        buy, payload = self.record(operation(w["id"]), "buy")
        before = m.path().read_bytes()
        bad = [
            operation(w["id"], quantity="100"),
            operation(w["id"], "SELL", "11"),
            operation(w["id"], economic_date="2019-12-31"),
            operation(w["id"], economic_date="2999-01-01"),
            operation(w["id"], quantity="-1"),
            operation(w["id"], price="NaN"),
            operation(w["id"], costs="-1"),
            operation(w["id"], quantity="1.5"),
            operation(w["id"], "SELL", "1", costs="1000.00"),
        ]
        for r in bad:
            with self.subTest(r=r), self.assertRaises(m.Invalid):
                m.post("preview", {"request": r})
        self.assertEqual(before, m.path().read_bytes())
        late = operation(w["id"], "SELL", "8", costs="0", economic_date="2020-01-04")
        self.record(late, "late")
        # Backdated sale makes the previously valid later sale impossible.
        with self.assertRaisesRegex(m.Invalid, "2020-01-04"):
            m.post(
                "preview",
                {
                    "request": operation(
                        w["id"], "SELL", "3", costs="0", economic_date="2020-01-03"
                    )
                },
            )
        with self.assertRaises(m.Invalid):
            m.post(
                "preview",
                {
                    "request": {
                        "kind": "CORRECTION",
                        "wallet": w["id"],
                        "target": buy["event_id"],
                        "reason": "anular",
                        "trade": None,
                    }
                },
            )
        r = operation(w["id"], quantity="1")
        preview = m.post("preview", {"request": r})
        self.record(operation(w["id"], quantity="2"), "concurrent")
        with self.assertRaisesRegex(m.Invalid, "carteira mudou"):
            m.post("confirm", confirmation(r, "stale", preview["preview_token"]))
        changed = {**payload, "request": operation(w["id"], quantity="11")}
        with self.assertRaisesRegex(m.Invalid, "dados diferentes"):
            m.post("confirm", changed)
        # SQLite transaction rolls back even if response construction fails.
        from unittest.mock import patch

        r = operation(w["id"], quantity="1")
        preview = m.post("preview", {"request": r})
        original, count = m.replay, 0

        def fault(history):
            nonlocal count
            count += 1
            if count == 4:
                raise RuntimeError("after insert before commit")
            return original(history)

        prior = m.path().read_bytes()
        with patch.object(m, "replay", fault), self.assertRaises(RuntimeError):
            m.post("confirm", confirmation(r, "rollback", preview["preview_token"]))
        self.assertEqual(m.path().read_bytes(), prior)

    def test_concurrent_confirmation_and_immutable_rows(self):
        w = self.create()
        r = operation(w["id"])
        p = m.post("preview", {"request": r})
        payload = confirmation(r, "concurrent", p["preview_token"])
        with ThreadPoolExecutor(max_workers=2) as pool:
            result = list(pool.map(lambda _: m.post("confirm", payload), range(2)))
        self.assertEqual(result[0]["event_id"], result[1]["event_id"])
        self.assertEqual(len(m.get({})["wallets"][0]["trades"]), 1)
        from contextlib import closing

        with closing(m.connect(write=True)) as conn, self.assertRaises(
            sqlite3.IntegrityError
        ):
            conn.execute("DELETE FROM events")

    def test_sale_costs_above_gross_require_cash_not_a_fictitious_cap(self):
        w = self.create()
        self.record(operation(w["id"]), "buy")
        d, _ = self.record(operation(w["id"], "SELL", "1", costs="30.00"), "fees")
        self.assertEqual(
            (d["wallet"]["cash"], d["wallet"]["realized_pnl"]), ("788.00", "-30.20")
        )
        empty = self.create("Sem caixa", capital="202.00")
        self.record(operation(empty["id"]), "empty-buy")
        with self.assertRaises(m.Invalid):
            m.post(
                "preview", {"request": operation(empty["id"], "SELL", "1", costs="30.00")}
            )

    def test_http_local_access_confirmation_and_reopen(self):
        with server.ReusableTCPServer(("127.0.0.1", 0), server.Handler) as web:
            thread = threading.Thread(target=web.serve_forever, daemon=True)
            thread.start()
            port = web.server_address[1]

            def call(method, path, body=None, headers=None):
                conn = http.client.HTTPConnection("127.0.0.1", port)
                conn.request(
                    method, path, json.dumps(body) if body else None, headers or {}
                )
                response = conn.getresponse()
                result = response.status, json.loads(response.read())
                conn.close()
                return result

            try:
                status, d = call("GET", "/api/portfolio/manual")
                self.assertEqual(status, 200)
                r = {
                    "kind": "CREATE",
                    "name": "Via web",
                    "nature": "EXTERNAL",
                    "capital": "500.00",
                    "start_date": "2020-01-01",
                }
                body = confirmation(r, "web")
                url = "/api/portfolio/manual/confirm"
                headers = {
                    "Origin": f"http://127.0.0.1:{port}",
                    "X-CSRF-Token": d["csrf_token"],
                    "Content-Type": "application/json",
                }
                self.assertEqual(call("POST", url, body)[0], 403)
                self.assertEqual(
                    call(
                        "POST", url, body, {**headers, "Origin": "https://evil.example"}
                    )[0],
                    403,
                )
                self.assertEqual(
                    call("POST", url, body, {**headers, "X-CSRF-Token": "wrong"})[0], 403
                )
                status, created = call("POST", url, body, headers)
                self.assertEqual(status, 200)
                wallet = created["wallet"]["id"]
                r = operation(wallet)
                status, p = call(
                    "POST", "/api/portfolio/manual/preview", {"request": r}, headers
                )
                self.assertEqual(status, 200)
                payload = confirmation(r, "web-trade", p["preview_token"])
                self.assertEqual(call("POST", url, payload, headers)[0], 200)
                self.assertTrue(call("POST", url, payload, headers)[1]["replayed"])
                self.assertEqual(call("POST", "/api/forward/run", {}, headers)[0], 403)
                self.assertEqual(
                    call("GET", "/api/portfolio/manual?wallet=h2:ai")[0], 400
                )
            finally:
                web.shutdown()
                thread.join()
        # Fresh process imports and replays exactly the same persisted catalog.
        env = {**os.environ, "HFL_MANUAL_ROOT": self.temp.name}
        code = "import sys;sys.path[:0]=['dashboard','scripts','.'];import server,json;print(json.dumps(server.manual_portfolio_api.get({})))"
        loaded = json.loads(
            subprocess.check_output(
                [sys.executable, "-B", "-c", code], cwd=PROJECT, env=env
            )
        )
        self.assertEqual(loaded["wallets"][0]["cash"], "298.00")
        self.assertEqual(loaded["wallets"][0]["id"], wallet)


def browser_check():
    base = PROJECT / "data/cache"
    base.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="hfl-personal-browser-", dir=base) as root:
        env = {**os.environ, "HFL_MANUAL_ROOT": root}
        env.pop("GEMINI_API_KEY", None)
        for flags in ([], ["--resume"]):
            child = subprocess.Popen(
                [sys.executable, "-B", __file__, "--serve"],
                cwd=PROJECT,
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
                text=True,
            )
            try:
                port = child.stdout.readline().strip()
                subprocess.run(
                    [
                        "node",
                        "tests/manual_portfolio_browser_check.mjs",
                        f"http://127.0.0.1:{port}",
                        "data/cache/manual-portfolio-ui",
                        *flags,
                    ],
                    cwd=PROJECT,
                    check=True,
                )
            finally:
                child.terminate()
                child.wait(timeout=10)


if __name__ == "__main__":
    if "--serve" in sys.argv:
        with server.ReusableTCPServer(("127.0.0.1", 0), server.Handler) as web:
            print(web.server_address[1], flush=True)
            web.serve_forever()
    elif "--browser" in sys.argv:
        browser_check()
    else:
        unittest.main()
