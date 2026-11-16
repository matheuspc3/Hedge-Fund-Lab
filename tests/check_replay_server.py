"""DP-37 read-only replay boundary; run with Python, no external network or real data."""
import http.client
import gzip
import os
import sys
import tempfile
import threading
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / "scripts"), str(ROOT / "dashboard")]
os.environ["HFL_DAILY_CYCLE"] = "0"
os.environ["HFL_MARKET_BASE_AUTOUPDATE"] = "0"
os.environ["HFL_RATES_OFFLINE"] = "1"
import server


def check(version="v1"):
    with tempfile.TemporaryDirectory(prefix="hfl-replay-http-") as folder:
        exports = Path(folder) / "exports"
        exports.mkdir()
        root_name = "REPLAY_ROOT" if version == "v1" else f"REPLAY_{version.upper()}_ROOT"
        previous_root = getattr(server, root_name)
        setattr(server, root_name, exports)
        try:
            with server.ReusableTCPServer(("127.0.0.1", 0), server.Handler) as httpd:
                thread = threading.Thread(target=httpd.serve_forever, daemon=True)
                thread.start()
                port = httpd.server_address[1]

                def request(path, method="GET", **headers):
                    conn = http.client.HTTPConnection("127.0.0.1", port, timeout=5)
                    conn.request(method, path, b"{}" if method == "POST" else None, headers)
                    response = conn.getresponse()
                    result = response.status, response.read(), dict(response.getheaders())
                    conn.close()
                    return result

                try:
                    route = server.REPLAY_ROUTE if version == "v1" else getattr(server, f"REPLAY_{version.upper()}_ROUTE")
                    for other in (server.REPLAY_ROUTE, server.REPLAY_V2_ROUTE, server.REPLAY_V3_ROUTE):
                        if other != route:
                            assert request(other)[0] == 503, "must not fall back to another version"
                    for name in sorted(server.REPLAY_FILES):
                        data = ("fake archived export " + name).encode()
                        (exports / name).write_bytes(data)
                        status, body, headers = request(route + name)
                        assert status == 200 and body == data, name
                        status, empty, head = request(route + name, "HEAD")
                        assert status == 200 and not empty
                        assert headers["Content-Length"] == head["Content-Length"] == str(len(data))
                        assert headers["Content-Type"] == head["Content-Type"]
                        assert headers["X-Content-Type-Options"] == "nosniff"
                    assert request(route)[1] == (exports / "index.html").read_bytes()
                    assert request(route + "calls-data.js")[2]["Content-Type"].startswith(("application/javascript", "text/javascript"))
                    assert request(route + "daily.csv")[2]["Content-Type"].startswith("text/csv")
                    raw = (exports / "index.html").read_bytes()
                    for accept in ("gzip", "br, gzip;q=0.5", "gzip;q=1.0"):
                        status, packed, headers = request(route, **{"Accept-Encoding": accept})
                        assert status == 200 and gzip.decompress(packed) == raw
                        assert headers["Content-Encoding"] == "gzip" and headers["Vary"] == "Accept-Encoding"
                        status, empty, head = request(route, "HEAD", **{"Accept-Encoding": accept})
                        assert status == 200 and not empty and head["Content-Encoding"] == "gzip"
                        assert "Content-Length" not in headers and "Content-Length" not in head
                    for accept in ("identity", "gzip;q=0", "gzip;q=0.0", "gzip;q=0.0001", "gzip;q=1.1", "xgzip"):
                        status, body, headers = request(route, **{"Accept-Encoding": accept})
                        assert status == 200 and body == raw and "Content-Encoding" not in headers
                    (exports / "index.html").write_bytes(b"<!doctype html><html><head></head>\n<body>\n<main>ok</main></body></html>")
                    status, body, headers = request(route)
                    assert status == 200 and b'class="hfl-shell" data-default-area="replay"' in body
                    assert b'data-area="replay"' in body and b'id="main"' in body
                    for target in (server.REPLAY_ROUTE, server.REPLAY_V2_ROUTE, server.REPLAY_V3_ROUTE):
                        assert f'href="{target}"'.encode() in body
                    assert headers["Content-Length"] == str(len(body))
                    (exports / "index.html").write_bytes(raw)
                    for method in ("GET", "HEAD"):
                        status, body, headers = request(route[:-1], method)
                        assert status == 308 and not body and headers["Location"] == route
                    status, body, _ = request("/laboratory")
                    assert status == 200 and server.REPLAY_ROUTE.encode() in body
                    assert "Replay abril–novembro".encode() in body
                    (exports / "manual.sqlite3").write_bytes(b"private book")
                    for name in ("manual.sqlite3", "abrir_explorador.py", "../index.html", "%2e%2e/index.html", "%69ndex.html", "//index.html", "folder/index.html", "index.html/", "..\\calls.json"):
                        assert request(route + name)[0] == 404, name
                    assert request(route, Host="outside.example")[0] == 403
                    assert request(route, Origin="https://outside.example")[0] == 403
                    public = os.environ.get("HFL_PUBLIC_HOST")
                    os.environ["HFL_PUBLIC_HOST"] = "replay.example.ts.net"
                    try:
                        assert request(route, Host="replay.example.ts.net", Origin="https://replay.example.ts.net")[0] == 200
                        assert request(route, Host="replay.example.ts.net", Origin="http://replay.example.ts.net")[0] == 403
                    finally:
                        if public is None:
                            os.environ.pop("HFL_PUBLIC_HOST", None)
                        else:
                            os.environ["HFL_PUBLIC_HOST"] = public
                    cross = {"Sec-Fetch-Site": "cross-site", "Sec-Fetch-Mode": "navigate", "Sec-Fetch-Dest": "document"}
                    assert request(route, **cross)[0] == 200
                    assert request(route[:-1], **cross)[0] == 308
                    assert request(route + "calls.json", **cross)[0] == 403
                    assert request(route, **{"Sec-Fetch-Site": "cross-site"})[0] == 403
                    post = {"Origin": f"http://127.0.0.1:{port}", "X-CSRF-Token": server.forward_jobs.JOBS.csrf}
                    assert request(route, "POST", **post)[0] == 404
                    assert request(route + "calls.json", "POST", **post)[0] == 404
                    (exports / "index.html").unlink()
                    status, body, headers = request(route)
                    assert status == 503 and "O replay ainda não está disponível".encode() in body
                    assert str(exports).encode() not in body
                    status, empty, head = request(route, "HEAD")
                    assert status == 503 and not empty and head["Content-Length"] == headers["Content-Length"]
                    (exports / "calls.json").unlink()
                    outside = Path(folder) / "private.json"
                    outside.write_bytes(b"not an export")
                    try:
                        (exports / "calls.json").symlink_to(outside)
                    except OSError:
                        print("SKIP: this Windows account cannot create file symlinks")
                    else:
                        assert request(route + "calls.json")[0] == 404
                finally:
                    httpd.shutdown()
                    thread.join()
        finally:
            setattr(server, root_name, previous_root)
    print("PASS replay GET/HEAD, downloads, canonical route, Lab link, private-file/traversal/origin/POST guards and unavailable-data state")


if __name__ == "__main__":
    # All versions use the same boundary; empty roots keep these checks data-free.
    with tempfile.TemporaryDirectory(prefix="hfl-replay-absent-") as absent:
        server.REPLAY_ROOT = Path(absent) / "v1"
        server.REPLAY_V2_ROOT = Path(absent) / "v2"
        server.REPLAY_V3_ROOT = Path(absent) / "v3"
        check()
        check("v2")
        check("v3")
