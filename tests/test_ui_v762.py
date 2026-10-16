"""V7.6.2 UX foundation: unified navigation, design system, contextual help, closed V1
paid action. A keyless dashboard is started on a free port; only GET requests are sent.
The browser checks (headless Chrome over DevTools, scripts/ui_check_v762.mjs) run when
Node and Chrome are available."""

import json
import os
import re
import shutil
import socket
import subprocess
import sys
import tempfile
import time
import unittest
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DASH = ROOT / "dashboard"
RUN = "radar-2026-10-09-recovery-01"
ROUTES = (
    "/",
    "/index.html",
    "/legacy",
    "/legacy/",
    "/logs",
    "/logs.html",
    "/h2",
    "/h2/",
    "/h2.html",
    "/paper",
    "/paper/",
    "/paper.html",
    "/radar",
    "/radar/",
    "/radar.html",
    "/portfolio",
    "/portfolio/",
    "/portfolio.html",
)
CHROME = next(
    (
        p
        for p in (
            "C:/Program Files/Google/Chrome/Application/chrome.exe",
            "/usr/bin/google-chrome",
            "/usr/bin/chromium",
        )
        if Path(p).exists()
    ),
    None,
)
REQUIRED_TERMS = {
    "rsi",
    "macd",
    "bollinger",
    "volatilidade",
    "drawdown",
    "sharpe",
    "correlacao",
    "consenso",
    "confianca-tecnica",
    "risk",
    "veto",
    "caixa-disponivel",
    "caixa-reservado",
    "recebivel",
    "d-mais-2",
    "peso-alvo",
    "exposicao",
    "preflight",
    "snapshot",
    "hash",
    "claim",
    "journal",
    "replay",
    "inferencia-paga",
    "proposta-validada",
    "proposta-rejeitada",
    "paper-trading",
    "backtesting",
}


def luminance(color):
    channels = [int(color[i : i + 2], 16) / 255 for i in (1, 3, 5)]
    channels = [
        c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4 for c in channels
    ]
    return 0.2126 * channels[0] + 0.7152 * channels[1] + 0.0722 * channels[2]


def contrast(a, b):
    hi, lo = sorted((luminance(a), luminance(b)), reverse=True)
    return (hi + 0.05) / (lo + 0.05)


def glossary_ids():
    text = (DASH / "glossary.js").read_text(encoding="utf-8")
    return re.findall(r"^  '?([a-z0-9-]+)'?: \{", text, re.M)


class Server(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with socket.socket() as s:
            s.bind(("127.0.0.1", 0))
            cls.port = s.getsockname()[1]
        env = {k: v for k, v in os.environ.items() if k != "GEMINI_API_KEY"}
        cls.proc = subprocess.Popen(
            [
                sys.executable,
                "-B",
                str(ROOT / "scripts/serve_dashboard_keyless.py"),
                str(cls.port),
            ],
            cwd=ROOT,
            env=env,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        cls.base = f"http://127.0.0.1:{cls.port}"
        for _ in range(120):
            try:
                urllib.request.urlopen(cls.base + "/shell.css", timeout=2)
                return
            except OSError:
                time.sleep(0.25)
        cls.proc.kill()
        raise RuntimeError("dashboard_did_not_start")

    @classmethod
    def tearDownClass(cls):
        cls.proc.terminate()
        cls.proc.wait(10)

    def get(self, path):
        try:
            with urllib.request.urlopen(self.base + path, timeout=30) as r:
                return r.status, r.read().decode("utf-8")
        except urllib.error.HTTPError as e:
            return e.code, ""

    # Navigation
    def test_every_route_served_with_one_global_navigation(self):
        for route in ROUTES:
            with self.subTest(route=route):
                status, body = self.get(route)
                self.assertEqual(status, 200)
                self.assertEqual(body.count('aria-label="Navegação principal"'), 1)
                self.assertEqual(
                    len(
                        re.findall(r'<a href="[^"]*" data-area="[a-z]+" data-env=', body)
                    ),
                    5,
                )
                self.assertNotIn('<nav class="header-nav"', body)
                self.assertNotIn('nav class="tabs"', body)
                self.assertNotIn('aria-label="Áreas do laboratório"', body)
                self.assertIsNone(
                    re.search(
                        r"Premium V\d|PREMIUM V\d",
                        re.search(r"<title>(.*?)</title>", body).group(1),
                    )
                )

    def test_deep_links_and_query_strings_still_served(self):
        for route in (
            f"/radar?run={RUN}",
            f"/portfolio?run={RUN}",
            "/radar?tickers=PETR4",
            "/portfolio?analysis=v7-" + "a" * 32,
            "/paper#sala",
        ):
            with self.subTest(route=route):
                self.assertEqual(self.get(route)[0], 200)

    def test_shared_assets_served_and_private_files_refused(self):
        for path in (
            "/design-system.css",
            "/glossary.js",
            "/ui.js",
            "/shell.css",
            "/shell.js",
        ):
            self.assertEqual(self.get(path)[0], 200, path)
        for path in ("/shell.html", "/server.py", "/platform_api.py", "/../.env"):
            self.assertEqual(self.get(path)[0], 404, path)

    def test_default_area_per_page(self):
        expected = {
            "/": "inicio",
            "/radar": "mercado",
            "/portfolio": "carteira",
            "/paper": "legacy",
            "/h2": "legacy",
            "/legacy": "legacy",
            "/logs": "auditoria",
        }
        for route, area in expected.items():
            body = self.get(route)[1]
            self.assertIn(f'data-default-area="{area}"', body)
            self.assertRegex(
                body, rf'data-area="{area}" data-env="[^"]+" aria-current="true"'
            )

    # Browser
    @unittest.skipUnless(
        shutil.which("node") and CHROME and not os.environ.get("HFL_SKIP_BROWSER"),
        "node/Chrome unavailable or HFL_SKIP_BROWSER set",
    )
    def test_browser_checks(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "ui_checks.json"
            done = subprocess.run(
                [
                    "node",
                    str(ROOT / "scripts/ui_check_v762.mjs"),
                    "checks",
                    self.base,
                    str(out),
                ],
                cwd=ROOT,
                capture_output=True,
                text=True,
                encoding="utf-8",
                timeout=900,
            )
            self.assertTrue(out.exists(), done.stdout[-2000:] + done.stderr[-2000:])
            report = json.loads(out.read_text(encoding="utf-8"))
        failures = [r for r in report["results"] if not r["ok"]]
        self.assertEqual(failures, [], done.stdout[-2000:] + done.stderr[-2000:])
        self.assertGreaterEqual(report["passed"], 100)


class Static(unittest.TestCase):
    def test_glossary_is_single_and_complete(self):
        ids = glossary_ids()
        self.assertEqual(len(ids), len(set(ids)))
        self.assertLessEqual(REQUIRED_TERMS, set(ids))
        used = set()
        for f in [*DASH.glob("*.html"), *DASH.glob("*.js")]:
            text = f.read_text(encoding="utf-8")
            used |= set(re.findall(r'data-help="([a-z0-9-]+)"', text))
            used |= set(
                re.findall(r"HFL\.help\('([a-z0-9-]+)'\)|H\('([a-z0-9-]+)'\)", text)
                and [
                    x
                    for t in re.findall(
                        r"HFL\.help\('([a-z0-9-]+)'\)|H\('([a-z0-9-]+)'\)", text
                    )
                    for x in t
                    if x
                ]
            )
        self.assertTrue(used and used <= set(ids), used - set(ids))
        for f in DASH.glob("*.html"):
            self.assertNotIn(
                "Não representa a probabilidade de lucro",
                f.read_text(encoding="utf-8"),
                f.name,
            )

    def test_tokens_meet_contrast(self):
        css = (DASH / "design-system.css").read_text(encoding="utf-8")

        def token(name):
            return re.search(rf"--{name}: (#[0-9a-f]{{6}});", css).group(1)

        surfaces = [token(n) for n in ("bg", "surface", "surface-2", "surface-3")]
        for s in surfaces:
            self.assertGreaterEqual(contrast(token("border-control"), s), 3.0)
            for t in (
                "text",
                "text-2",
                "muted",
                "link",
                "state-ok",
                "state-warn",
                "state-error",
                "state-info",
                "state-synthetic",
                "state-paid",
            ):
                self.assertGreaterEqual(contrast(token(t), s), 4.5, t)
        self.assertNotRegex(
            (DASH / "shell.css").read_text(encoding="utf-8"), r":root\s*\{"
        )

    def test_closed_v1_triggers_and_no_new_paid_path(self):
        js = (DASH / "global-workflow.js").read_text(encoding="utf-8")
        self.assertIn("const V1_CLOSED=true", js)
        for listener in (
            "workflow-prepare",
            "workflow-preflight",
            "workflow-run",
            "workflow-authorize",
        ):
            self.assertRegex(
                js,
                rf"el\('{listener}'\)\.addEventListener\('click',(?:async)?\(\)=>\{{if\(V1_CLOSED",
            )
        self.assertIn("if(V1_CLOSED&&command!=='replay')return fail(", js)
        html = (DASH / "portfolio.html").read_text(encoding="utf-8")
        self.assertNotIn('/global-workflow.js', html)
        self.assertNotIn('id="workflow-run"', html)
        self.assertNotIn('id="workflow-authorize"', html)
        self.assertNotIn("method:'POST'", (DASH / "monitoring.js").read_text(encoding="utf-8"))
        self.assertIn("encerrado para novas inferências", html)
        paid = {
            (f.name, m)
            for f in DASH.glob("*.html")
            for m in re.findall(
                r'id="([a-z-]+)"[^>]*data-action="paid"', f.read_text(encoding="utf-8")
            )
        }
        self.assertEqual(
            paid,
            {
                ("radar.html", "execute"),
            },
        )
        senders = [
            f.name
            for f in DASH.glob("*.js")
            if "global-'+command" in f.read_text(encoding="utf-8")
        ]
        self.assertEqual(senders, ["global-workflow.js"])

    def test_scientific_identifiers_untouched(self):
        sealed = (
            json.loads(
                (
                    ROOT
                    / "data/global_pm/hfl_global_pm_v1/v7-5a78ea5d15214e37bcae18f167ffcee3/result.json"
                ).read_text(encoding="utf-8")
            )
            if (ROOT / "data/global_pm/hfl_global_pm_v1").exists()
            else None
        )
        if sealed:
            self.assertEqual(sealed["status"], "REJECTED_BY_VALIDATOR")
            v2 = json.loads(
                (
                    ROOT
                    / "data/global_pm/hfl_global_pm_v2/v74-76d07c0d32444cecaf07e875deacb519/result.json"
                ).read_text(encoding="utf-8")
            )
            self.assertEqual(v2["status"], "VALID_PROPOSAL")
        ui = (DASH / "ui.js").read_text(encoding="utf-8")
        for code in (
            "VALID_PROPOSAL",
            "REJECTED_BY_VALIDATOR",
            "PREPARED",
            "BLOCKED",
            "RUNNING",
            "COMPLETED",
            "EXPIRED",
            "READ_ONLY",
            "SYNTHETIC",
            "OFFICIAL",
            "CONSULTATIVE_SANDBOX",
        ):
            self.assertIn(f"{code}: [", ui)


if __name__ == "__main__":
    unittest.main()
