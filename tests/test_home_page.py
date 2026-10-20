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
    assert "The existing lineage check flags no controls for review." in hero
    # Nothing on the landing page reveals what the investigation finds.
    assert "With the detective" not in text
    assert f"{case['agent_recommended']} safety checks" not in text
    p = experience["portfolio"]
    for figure in (p["agent_found_key"], p["new_right"], p["key_affected"]):
        assert str(figure) not in text
    assert "always has gaps" not in text
    assert "can have gaps" in text


def test_one_header_is_the_only_way_between_pages(page, experience):
    for route in (
        "#/home",
        "#/overview",
        "#/room/results",
        "#/handbook/investigator",
        "#/decision?case=CHG-027",
    ):
        page.goto(page.base + route)
        page.wait_for_selector("main > *")
        page.wait_for_timeout(200)
        labels = page.locator("#sitenav a").all_inner_texts()
        assert [x.replace("\n", " ") for x in labels] == [
            "Home",
            "Walkthrough",
            "Product overview",
            "Evidence room",
            "Technical handbook",
        ]
        # No page body repeats a link to another page.
        body_links = page.locator(
            "main a[href^='#/home'], main a[href^='#/overview'], "
            "main a[href^='#/room'], main a[href^='#/handbook'], main a[href^='#/change'], "
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
    # The walkthrough opens on the test bank, before the change.
    assert "#/bank?case=CHG-027" in page.url
    assert page.locator(".bank-types").count() == 1
    page.locator("#next-step").click()
    page.wait_for_selector(".record")
    assert "#/change?case=CHG-027" in page.url
    assert "finds nothing to review" in page.locator("h1.title").inner_text()
    assert page.locator("#journey").is_visible()


def test_overview_figures_match_the_recorded_run(page, experience):
    p = experience["portfolio"]
    page.goto(page.base + "#/overview")
    page.wait_for_selector(".ov-m")
    text = page.locator("main").inner_text()
    assert f"{p['agent_found_key']} of {p['key_misses']}" in text
    assert f"{p['new_right']} of {p['new_total']}" in text
    assert str(p["added_affected"]) in text and str(p["added_unaffected"]) in text
    uncertain = p["added_items"] - p["new_total"]
    assert (
        f"{p['added_items']} added items are {p['new_total']} new recommendations"
        f" and {uncertain} findings sent to a person" in text
    )
    assert "must not be added together" in text
    assert "Hidden impacts, found early" not in text


def test_home_fits_a_phone(page):
    page.set_viewport_size({"width": 390, "height": 844})
    open_home(page)
    overflow = page.evaluate("document.documentElement.scrollWidth - innerWidth")
    page.set_viewport_size({"width": 1440, "height": 900})
    assert overflow <= 0


def test_next_button_walks_every_step(page):
    page.goto(page.base + "#/bank?case=CHG-027")
    page.wait_for_selector("h1.title")
    for step in ("change", "blindspot", "investigate", "consequence", "decision"):
        assert page.locator("#journey a.up-next").count() == 1
        page.locator("#next-step").click()
        page.wait_for_timeout(400)
        assert f"#/{step}?case=CHG-027" in page.url
    # The walkthrough's last step hands over to the product overview.
    assert "Product overview" in page.locator("#next-step").inner_text()
    page.locator("#next-step").click()
    page.wait_for_selector(".ov-m")
    assert "#/overview" in page.url


def test_reference_codes_are_explained(page):
    page.goto(page.base + "#/bank?case=CHG-027")
    page.wait_for_selector(".bank-types")
    key = page.locator(".bank-types").inner_text()
    for code, kind in (("C", "Controls"), ("S", "Systems"), ("I", "Interfaces")):
        assert code in key and kind in key
    # The test bank is the first stop of the walkthrough.
    assert page.locator("#journey a").first.inner_text().endswith("The test bank")
    page.goto(page.base + "#/investigate?case=CHG-027&control=C02")
    page.wait_for_selector("#inspector.open")
    reasons = page.locator("#inspector .verdict").first.inner_text()
    assert "Screening request interface (I02)" in reasons
    assert "S03, the Screening Engine" in reasons  # already named: not repeated


def test_replay_hover_gives_the_basis_of_each_decision(page):
    page.goto(page.base + "#/investigate?case=CHG-027")
    page.wait_for_selector("#end")
    page.locator("#end").click()
    page.wait_for_timeout(300)
    page.locator(".g-node").filter(has_text="C02 ").first.hover()
    page.wait_for_timeout(200)
    t = page.locator("#tip").inner_text()
    for part in (
        "Recommended for owner assessment",
        "both say this control is affected",
        "Evidence strength",
        "Strong",
        "worked out by the AI",
    ):
        assert part in t
    assert "not an AI confidence percentage" in t  # no model probability exists


def test_handbook_shows_the_prompts_of_the_recorded_run(page, experience):
    page.goto(page.base + "#/handbook/investigator")
    page.wait_for_selector(".prompt-d summary")
    page.locator(".prompt-d summary").click()
    shown = page.locator("pre.prompt").inner_text()
    assert shown.strip() == experience["prompts"]["investigator"].strip()
    page.goto(page.base + "#/handbook/verifier")
    page.wait_for_selector(".prompt-d summary")
    page.locator(".prompt-d summary").click()
    assert page.locator("pre.prompt").inner_text().strip() == (
        experience["prompts"]["verifier"].strip()
    )
    page.goto(page.base + "#/handbook/degradation")
    page.wait_for_selector("main h1")
    assert "71 of 237" in page.locator("main").inner_text()
    # Old evidence-room links to moved pages land in the handbook.
    page.goto(page.base + "#/room/architecture")
    page.wait_for_timeout(500)
    assert "#/handbook/architecture" in page.url


def test_first_button_is_visible_without_scrolling(page):
    # A short laptop browser window, after browser and platform bars.
    page.set_viewport_size({"width": 1280, "height": 600})
    open_home(page)
    box = page.locator('a[href="#problem"]').bounding_box()
    page.set_viewport_size({"width": 1440, "height": 900})
    assert box["y"] + box["height"] <= 520


def test_evidence_room_counts_reconcile_on_screen(page, experience):
    p = experience["portfolio"]
    page.goto(page.base + "#/room/results?case=CHG-027")
    page.wait_for_selector("tr.total")
    text = page.locator("main").inner_text()
    assert f"Show {p['added_affected']} affected" in text
    assert f"Show {p['added_unaffected']} not affected" in text
    assert page.locator("tr.total .num").inner_text().strip() == str(p["key_affected"])
    page.locator("[data-rec=addAff]").click()
    page.wait_for_timeout(200)
    row = page.locator("tr.rec-row")
    assert row.count() == 1 and row.locator("button.rec").count() == p["added_affected"]
    # it opens directly below the row of the button that was clicked
    assert page.locator("[data-rec=addAff]").locator("xpath=ancestor::tr/following-sibling::tr[1]").get_attribute("class") == "rec-row"
    page.locator("#rep-btn").click()
    page.wait_for_timeout(200)
    out = page.locator("tr.rec-row").inner_text()
    assert "8 of 10 affected key controls" in out


def test_case_persists_and_back_works(page):
    page.goto(page.base + "#/consequence?case=CHG-027")
    page.wait_for_selector("#estates .cell")
    page.select_option("#case", "CHG-015")
    page.wait_for_timeout(400)
    assert "#/consequence?case=CHG-015" in page.url
    page.locator("#sitenav a[data-nav=room]").click()
    page.wait_for_selector(".room")
    assert "case=CHG-015" in page.url
    page.go_back()
    page.wait_for_selector("#estates .cell")
    assert "#/consequence?case=CHG-015" in page.url
    assert page.locator("#case").input_value() == "CHG-015"
    assert "case=CHG-015" in page.locator(
        "#sitenav a[data-nav=walkthrough]"
    ).get_attribute("href")
    # A deep link to one control opens its evidence.
    page.goto(page.base + "#/investigate?case=CHG-024&control=C03")
    page.wait_for_selector("#inspector.open")
    assert "C03" in page.locator("#inspector .cid").inner_text()
    assert "CHG-024" in page.locator("#inspector .cid").inner_text()


def test_change_rows_open_their_decisions_in_place(page, experience):
    """Clicking a change shows its decisions directly below it, not elsewhere on the page."""
    page.goto(page.base + "#/room/changes?case=CHG-027")
    page.wait_for_selector(".cl-item")
    item = page.locator(".cl-item").nth(1)
    assert item.locator(".cl-body").is_hidden()
    item.locator(".cl-row").click()
    body = item.locator(".cl-body")
    assert body.is_visible()
    row_box, body_box = item.locator(".cl-row").bounding_box(), body.bounding_box()
    assert abs(body_box["y"] - (row_box["y"] + row_box["height"])) < 4
    assert body.locator("tr[data-c]").count() > 0
    item.locator(".cl-row").click()
    assert body.is_hidden()


def test_no_sixty_percent_damage_level_is_shown(page):
    for r in ["#/room/results", "#/handbook/degradation", "#/consequence", "#/overview"]:
        page.goto(page.base + r + "?case=CHG-027")
        page.wait_for_timeout(600)
        assert "60%" not in page.locator("main").inner_text()
