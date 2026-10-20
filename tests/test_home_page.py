"""The landing page sets up the example change without giving away its result.

Runs the real page in a headless browser. Skipped where Playwright and its
browser are not installed (the offline CI job), run wherever they are.
"""

import json
import threading
from http.server import ThreadingHTTPServer
from pathlib import Path

import pytest

sync_api = pytest.importorskip("playwright.sync_api")

from app.server import Handler  # noqa: E402

DATA = Path(__file__).resolve().parents[1] / "app" / "web" / "data"


@pytest.fixture(scope="module")
def experience():
    return json.loads((DATA / "experience.json").read_text())


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
        errors = []
        pg.on("pageerror", lambda e: errors.append(str(e)))
        pg.base = base
        pg.errors = errors
        yield pg
        browser.close()
    srv.shutdown()


def open_home(pg):
    pg.goto(pg.base)
    pg.wait_for_selector(".h-hero")
    return pg.locator("main").inner_text()


def test_home_is_the_front_door(page):
    open_home(page)
    assert page.url.endswith("/") or "#/home" in page.url
    assert page.title().startswith("Find the controls a change could break")
    assert not page.errors


def test_home_sets_up_the_change_but_keeps_the_answer(page, experience):
    text = open_home(page)
    case = next(c for c in experience["cases"] if c["id"] == "CHG-027")
    hero = page.locator(".h-case").inner_text()
    assert "CHG-027" in hero
    assert "The existing check flags no controls for review." in hero
    # Nothing on the landing page reveals what the investigation finds.
    assert "With the detective" not in text
    assert f"{case['agent_recommended']} safety checks" not in text
    p = experience["portfolio"]
    for figure in (p["agent_found_key"], p["new_right"], p["key_affected"]):
        assert str(figure) not in text
    assert "always has gaps" not in text
    assert "can have gaps" in text


def test_one_header_is_the_only_way_between_pages(page, experience):
    for route in ("#/home", "#/overview", "#/room/results", "#/decision?case=CHG-027"):
        page.goto(page.base + route)
        page.wait_for_selector("main > *")
        page.wait_for_timeout(200)
        labels = page.locator("#sitenav a").all_inner_texts()
        assert [x.replace("\n", " ") for x in labels] == [
            "Home",
            "Walkthrough",
            "Product overview",
            "Evidence room",
        ]
        # No page body repeats a link to another page.
        body_links = page.locator(
            "main a[href^='#/home'], main a[href^='#/overview'], "
            "main a[href^='#/room'], main a[href^='#/change'], "
            "main a[href^='#/investigate'], main [data-demo], main [data-go]"
        )
        room_nav = page.locator("main .room nav a")
        assert body_links.count() == room_nav.count(), route
    # Walkthrough steps only inside the walkthrough.
    page.goto(page.base + "#/room/results")
    page.wait_for_timeout(200)
    assert not page.locator("#subbar").is_visible()
    page.goto(page.base + "#/home")
    page.wait_for_selector(".h-hero")
    page.locator("#sitenav a[data-nav=walkthrough]").click()
    page.wait_for_selector("h1.title")
    assert "#/change?case=CHG-027" in page.url
    assert "finds nothing to review" in page.locator("h1.title").inner_text()
    assert page.locator("#journey").is_visible()


def test_overview_figures_match_the_recorded_run(page, experience):
    p = experience["portfolio"]
    page.goto(page.base + "#/overview")
    page.wait_for_selector(".h-benefits")
    text = page.locator("main").inner_text()
    surfaced = p["check_found_key"] + p["agent_found_key"]
    assert f"{surfaced}\nof {p['key_affected']}" in text or (
        f"{surfaced} of {p['key_affected']}" in text
    )
    assert str(p["key_routed"]) in text
    assert f"{p['key_silent']} affected key check, out of {p['key_affected']}" in text


def test_home_fits_a_phone(page):
    page.set_viewport_size({"width": 390, "height": 844})
    open_home(page)
    overflow = page.evaluate("document.documentElement.scrollWidth - innerWidth")
    page.set_viewport_size({"width": 1440, "height": 900})
    assert overflow <= 0


def test_next_button_walks_all_five_steps(page):
    page.goto(page.base + "#/change?case=CHG-027")
    page.wait_for_selector("h1.title")
    for step in ("blindspot", "investigate", "consequence", "decision"):
        assert page.locator("#journey a.up-next").count() == 1
        page.locator("#next-step").click()
        page.wait_for_timeout(400)
        assert f"#/{step}?case=CHG-027" in page.url
    assert not page.locator("#next-step").is_visible()


def test_reference_codes_are_explained(page):
    page.goto(page.base + "#/change?case=CHG-027")
    page.wait_for_selector(".codekey")
    assert "C control, S system, I interface" in page.locator(".codekey").inner_text()
    page.goto(page.base + "#/investigate?case=CHG-027&control=C02")
    page.wait_for_selector("#inspector.open")
    reasons = page.locator("#inspector .verdict").first.inner_text()
    assert "Screening request interface (I02)" in reasons
    assert "Screening Engine (S03)" in reasons
