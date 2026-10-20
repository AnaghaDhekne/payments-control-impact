"""The experience server: pages, data, PDF summary and the assistant fallback."""

import json
import threading
import urllib.request
from http.server import ThreadingHTTPServer

import pytest

from app.server import Handler, results_summary


@pytest.fixture(scope="module")
def base():
    srv = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    yield f"http://127.0.0.1:{srv.server_address[1]}"
    srv.shutdown()


def get(url):
    with urllib.request.urlopen(url, timeout=10) as r:
        return r.status, r.headers.get("Content-Type", ""), r.read()


def test_pages_and_data(base):
    status, ctype, body = get(base + "/")
    assert status == 200 and b"Control Impact Detective" in body
    for path in [
        "/js/main.js",
        "/js/screens.js",
        "/js/room.js",
        "/js/home.js",
        "/js/graph.js",
        "/css/app.css",
        "/data/graph.json",
        "/data/cases/CHG-003.json",
        "/data/cases/CHG-027.json",
    ]:
        assert get(base + path)[0] == 200
    e = json.loads(get(base + "/data/experience.json")[2])
    assert e["portfolio"]["agent_found_key"] == 113


def test_summary_pdf(base):
    status, ctype, body = get(base + "/summary.pdf")
    assert status == 200 and ctype == "application/pdf" and body.startswith(b"%PDF")


def test_ask_never_fails_hard(base):
    req = urllib.request.Request(
        base + "/api/ask",
        data=json.dumps({"question": "What was recovery?"}).encode(),
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=60) as r:
        assert r.status == 200 and json.loads(r.read())["answer"]


def test_assistant_summary_matches_export():
    s = results_summary()
    assert (
        "113 of the 144" in s
        and "331 genuinely affected" in s
        and "not a completed review" in s
    )


def test_assistant_can_list_every_control():
    text = results_summary()
    assert "All 101 controls" in text
    assert "C02 | Payment parties are sanctions screened before release | key" in text
    assert "S03 | Screening Engine | system" in text
    assert "CHG-024 |" in text
