"""DP-16: Legacy web boundary, aliases and an active home independent of H2."""

import http.client
import json
import sys
import threading
from contextlib import ExitStack
from pathlib import Path
from unittest.mock import patch

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / "scripts"), str(ROOT / "dashboard")]
import server  # noqa: E402


@pytest.fixture
def web():
    with server.ReusableTCPServer(("127.0.0.1", 0), server.Handler) as httpd:
        thread = threading.Thread(target=httpd.serve_forever, daemon=True)
        thread.start()
        yield httpd.server_address[1]
        httpd.shutdown()
        thread.join()


def request(port, path, method="GET", **headers):
    connection = http.client.HTTPConnection("127.0.0.1", port, timeout=20)
    connection.request(method, path, b"{}" if method == "POST" else None, headers)
    response = connection.getresponse()
    result = response.status, response.read().decode(), dict(response.getheaders())
    connection.close()
    return result


@pytest.mark.parametrize(
    "command",
    [
        "prepare",
        "preflight",
        "run",
        "benchmarks",
        "supervision/sync",
        "supervision/approve",
        "supervision/reject",
        "supervision/cancel",
        "scenario",
        "reconcile",
        "future-command",
    ],
)
def test_legacy_posts_never_dispatch_even_with_valid_csrf(web, command):
    with (
        patch.object(
            server.forward_jobs.JOBS, "start", side_effect=AssertionError("job")
        ),
        patch.object(
            server.forward_api, "supervise", side_effect=AssertionError("write")
        ),
        patch.object(
            server.market_api, "scenario", side_effect=AssertionError("scenario")
        ),
    ):
        for suffix in ("", "?confirm=true"):
            status, body, _ = request(
                web,
                "/api/forward/" + command + suffix,
                "POST",
                Origin=f"http://127.0.0.1:{web}",
                **{
                    "X-CSRF-Token": server.forward_jobs.JOBS.csrf,
                    "Content-Type": "application/json",
                },
            )
            assert status == 403 and json.loads(body)["error"] == "legacy_read_only"


def test_h2_posts_closed_but_active_dispatch_preserved(web):
    headers = {
        "Origin": f"http://127.0.0.1:{web}",
        "X-CSRF-Token": server.forward_jobs.JOBS.csrf,
    }
    assert request(web, "/api/h2/run", "POST", **headers)[0] == 403
    for route, handler in (
        ("/api/radar/prepare", "_handle_radar"),
        ("/api/platform/global-replay", "_handle_platform"),
    ):

        def dispatch(self, body):
            assert body == b"{}"
            return self._send_json({"active_dispatch": True})

        with patch.object(server.Handler, handler, dispatch):
            status, body, _ = request(web, route, "POST", **headers)
            assert status == 200 and json.loads(body)["active_dispatch"]


def test_hub_aliases_head_query_and_cross_site_navigation(web):
    for route, title in (
        ("/legacy", "Acervo histórico"),
        ("/legacy/paper", "Piloto PETR4"),
        ("/legacy/h2", "Experimento H2"),
        ("/legacy/backtests", "Backtests históricos"),
        ("/paper.html", "Piloto PETR4"),
        ("/h2/", "Experimento H2"),
        ("/index.html", "Backtests históricos"),
    ):
        url = route + "?source=provisional&wallet=h2%3Aai"
        status, body, headers = request(web, url)
        assert status == 200 and title in body
        assert 'data-default-area="legacy"' in body
        assert "documentação do TCC" in body
        head, empty, head_headers = request(web, url, "HEAD")
        assert head == 200 and not empty
        assert headers["Content-Length"] == head_headers["Content-Length"]
        assert (
            request(
                web,
                url,
                **{
                    "Sec-Fetch-Site": "cross-site",
                    "Sec-Fetch-Mode": "navigate",
                    "Sec-Fetch-Dest": "document",
                },
            )[0]
            == 200
        )
    body = request(web, "/")[1]
    primary = body.split('aria-label="Navegação principal">')[1].split("</nav>")[0]
    assert all(
        label in primary
        for label in ("Carteira", "Operações", "Agentes", "Comparação", "Dados")
    )
    assert all(
        label not in primary for label in ("Legacy", "Pesquisa", "Operação diária PETR4")
    )
    assert 'class="hfl-archive"' in body


@pytest.mark.parametrize(
    "route,area",
    [
        ("/operations", "operacoes"),
        ("/comparison", "comparacao"),
        ("/wallets/new", "inicio"),
        ("/dividends", "inicio"),
        ("/data", "mercado"),
        ("/laboratory", "carteira"),
    ],
)
def test_redesigned_routes_get_head_and_shared_assets(web, route, area):
    status, body, headers = request(web, route)
    assert status == 200 and f'data-default-area="{area}"' in body
    assert "/product.css?v=1" in body and "/product.js?v=1" in body
    head, empty, head_headers = request(web, route, "HEAD")
    assert head == 200 and not empty
    assert headers["Content-Length"] == head_headers["Content-Length"]
    assert request(web, "/product.css")[0] == request(web, "/product.js")[0] == 200


def test_active_overview_never_reads_independent_h2(web):
    api = server.platform_api
    with ExitStack() as stack:
        for obj, name in (
            (api.forward, "portfolios"),
            (api.forward, "decision"),
            (api.forward, "supervision"),
            (api, "forward_integrity"),
            (api.h2_api, "status"),
            (api.forward.fwd, "last_closed_session"),
            (api.market_api, "session_clock"),
            (api.forward_jobs.JOBS, "status"),
        ):
            stack.enter_context(patch.object(obj, name, side_effect=AssertionError(name)))
        status, body, _ = request(web, "/api/platform/overview")
        assert status == 200
        data = json.loads(body)
        assert data["read_only"] and data["execution_multiasset_available"] is False
        assert (
            not {"wallets", "decision", "supervision", "attention", "scientific"}
            & data.keys()
        )
        assert all(j["module"] != "H2" for j in data["jobs"].get("data", []))
        assert request(web, "/api/platform/jobs")[0] == 200


def test_historical_gets_are_still_available(web):
    for endpoint, obj, name, value in (
        ("/api/forward/portfolios", server.forward_api, "portfolios", {"wallets": []}),
        ("/api/forward/history", server.forward_api, "history", []),
        (
            "/api/forward/supervision",
            server.forward_api,
            "supervision",
            {"pending": True},
        ),
        ("/api/h2/status", server.h2_api, "status", {"historical": True}),
    ):
        with patch.object(obj, name, return_value=value):
            status, body, _ = request(web, endpoint)
            assert status == 200 and json.loads(body) == value
