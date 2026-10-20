"""Every claim spoken in the demo script (docs/demo-script.md) is on screen.

Each entry is (step, route, action, text that must be visible). Runs the real
app in a headless browser; skipped where Playwright and its browser are absent.
"""

import threading
from http.server import ThreadingHTTPServer

import pytest

sync_api = pytest.importorskip("playwright.sync_api")

from app.server import Handler  # noqa: E402

CLAIMS = [
    ("1 Opening", "#/home", None, "Banks protect payments with safety checks"),
    (
        "1 Opening",
        "#/home",
        None,
        "The existing lineage check flags no controls for review.",
    ),
    ("1 Opening", "#/home", None, "What might the existing lineage check have missed?"),
    (
        "2 Change",
        "#/change?case=CHG-027",
        None,
        "The impact check finds nothing to review.",
    ),
    ("2 Change", "#/change?case=CHG-027", None, "Screening request interface"),
    ("3 Blind spot", "#/blindspot?case=CHG-027", "reveal", "0 of 20"),
    ("3 Blind spot", "#/blindspot?case=CHG-027", "reveal", "13 of 24"),
    (
        "3 Blind spot",
        "#/blindspot?case=CHG-027",
        "reveal",
        "Screening Engine (S03) → Payment parties are sanctions screened before release (C02)",
    ),
    (
        "3 Blind spot",
        "#/blindspot?case=CHG-027",
        "reveal",
        "Why it matters to the bank:",
    ),
    (
        "4 Investigation",
        "#/investigate?case=CHG-027&control=C02",
        None,
        "Screening request interface",
    ),
    (
        "4 Investigation",
        "#/investigate?case=CHG-027&control=C02",
        None,
        "screened before payment release",
    ),
    (
        "4 Investigation",
        "#/investigate?case=CHG-027&control=C02",
        None,
        "The independent verifier agreed.",
    ),
    (
        "4 Investigation",
        "#/investigate?case=CHG-027&control=C02",
        None,
        "recommended for its owner to assess",
    ),
    (
        "4 Investigation",
        "#/investigate?case=CHG-027&control=C02",
        None,
        "worked out by the AI",
    ),
    ("5 Consequence", "#/consequence?case=CHG-027", None, "78.5%"),
    ("5 Consequence", "#/consequence?case=CHG-027", None, "113"),
    ("5 Consequence", "#/consequence?case=CHG-027", None, "of 144"),
    ("5 Consequence", "#/consequence?case=CHG-027", None, "95% range 71.1%–84.4%"),
    ("5 Consequence", "#/consequence?case=CHG-027", None, "262 of its 280"),
    (
        "5 Consequence",
        "#/consequence?case=CHG-027",
        None,
        "30 were sent to a person and 1 was not surfaced",
    ),
    ("5 Consequence", "#/room/results", None, "49.5%"),
    ("5 Consequence", "#/room/results", None, "57.6%"),
    ("7 Decision", "#/decision?case=CHG-027", None, "331 of the 406"),
    (
        "7 Decision",
        "#/decision?case=CHG-027",
        None,
        "which is the costly outcome",
    ),
    (
        "7 Decision",
        "#/decision?case=CHG-027",
        None,
        "Steadier decisions from run to run.",
    ),
    (
        "7 Decision",
        "#/decision?case=CHG-027",
        None,
        "second check on key controls marked not affected",
    ),
    (
        "6 Weaker case",
        "#/change?case=CHG-015",
        None,
        "The impact check flags 7 controls for review.",
    ),
    (
        "6 Weaker case",
        "#/consequence?case=CHG-015",
        None,
        "The detective recommended 3 (3 actually affected) and sent 10 to a person",
    ),
    (
        "7 Decision",
        "#/decision?case=CHG-027",
        None,
        "Ready for control owners to judge.",
    ),
    (
        "7 Decision",
        "#/decision?case=CHG-027",
        None,
        "all 30 key controls sent to a person",
    ),
    ("7 Decision", "#/decision?case=CHG-027", None, "93.6%"),
    ("7 Decision", "#/decision?case=CHG-027", None, "expected: none"),
    ("7 Decision", "#/decision?case=CHG-027", None, "The choice rests with leadership"),
]


@pytest.fixture(scope="module")
def page():
    srv = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    base = f"http://127.0.0.1:{srv.server_address[1]}/"
    with sync_api.sync_playwright() as p:
        try:
            browser = p.chromium.launch()
        except Exception as err:  # browser binary not installed
            pytest.skip(f"no browser: {err}")
        pg = browser.new_page(viewport={"width": 1440, "height": 900})
        pg.base = base
        yield pg
        browser.close()
    srv.shutdown()


@pytest.mark.parametrize("step,route,action,text", CLAIMS)
def test_spoken_claim_is_on_screen(page, step, route, action, text):
    page.goto(page.base + "#/home")  # reset the route so the next goto renders
    page.goto(page.base + route)
    page.wait_for_selector("main > *")
    page.wait_for_timeout(300)
    if action == "reveal":
        page.click("[data-mode=complete]")
        page.wait_for_timeout(200)
    page.evaluate("document.querySelectorAll('details').forEach((d) => (d.open = true))")  # one click away counts
    shown = page.locator("body").inner_text()
    assert text in shown, f"{step}: '{text}' not on {route}"
