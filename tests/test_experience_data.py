"""The client-facing experience shows only figures that trace back to the source.

These tests read the committed JSON in app/web/data and check it against the
recorded run archive and the benchmark code, so a stale or hand-edited export
fails the build.
"""

import json
import tarfile
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "app" / "web" / "data"
ARCHIVE = ROOT / "results" / "detective_runs.tar.gz"


@pytest.fixture(scope="module")
def experience():
    return json.loads((DATA / "experience.json").read_text())


@pytest.fixture(scope="module")
def cases():
    return {
        p.stem: json.loads(p.read_text()) for p in (DATA / "cases").glob("CHG-*.json")
    }


@pytest.fixture(scope="module")
def run_metrics():
    with tarfile.open(ARCHIVE) as t:
        m = next(
            x
            for x in t.getmembers()
            if x.name.lstrip("./") == "heldout-final/run1/metrics.json"
        )
        return json.load(t.extractfile(m))["summary"]


def test_headline_matches_recorded_run(experience, run_metrics):
    p = experience["portfolio"]
    assert p["changes"] == 18
    assert p["key_misses"] == run_metrics["key_misses"] == 144
    assert p["agent_found_key"] == run_metrics["key_recovered"] == 113
    assert p["added_items"] == run_metrics["added_review_items"] == 406
    assert p["added_unaffected"] == run_metrics["avoidable_review_items"] == 75
    assert p["check_items"] == run_metrics["baseline_workload"] == 64
    assert p["uncertain"] == run_metrics["uncertain_controls"] == 126


def test_key_controls_partition(experience):
    p = experience["portfolio"]
    assert p["key_affected"] == 162
    assert p["check_found_key"] == 18
    assert (
        p["check_found_key"] + p["agent_found_key"] + p["key_routed"] + p["key_silent"]
        == 162
    )
    assert (p["key_routed"], p["key_silent"]) == (30, 1)
    assert p["silent"] == [{"change": "CHG-024", "control": "C03"}]


def test_review_items_are_not_called_waste(experience):
    p = experience["portfolio"]
    assert p["added_affected"] == 331
    assert p["added_affected"] + p["added_unaffected"] == p["added_items"]


def test_cases_agree_with_portfolio(experience, cases):
    assert len(cases) == 18
    for row in experience["cases"]:
        c = cases[row["id"]]
        routes = {d["route"] for d in c["decisions"]}
        assert routes <= {"check", "recommended", "review", "not_affected", "undecided"}
        assert (
            c["counts"]["key_found_by_agent"]
            + c["counts"]["key_routed"]
            + c["counts"]["key_silent"]
            == c["counts"]["key_misses"]
        )
    assert sum(c["counts"]["key_found_by_agent"] for c in cases.values()) == 113


def test_case_graph_is_consistent(cases):
    graph = json.loads((DATA / "graph.json").read_text())
    nodes = {n["id"] for n in graph["nodes"]}
    edges = {e["id"] for e in graph["edges"]}
    assert len(nodes) == 148 and len(edges) == 238
    for c in cases.values():
        assert set(c["focus"]["nodes"]) <= nodes
        assert set(c["focus"]["edges"]) <= edges
        assert set(c["removed_links"]) <= edges
        assert set(c["focus"]["layout"]["pos"]) == set(c["focus"]["nodes"])
        for d in c["decisions"]:
            assert d["control"] in nodes


def test_replay_is_recorded_not_invented(cases):
    c = cases["CHG-003"]
    assert c["steps"][0]["action"] == "explore_node" and c["steps"][0]["explored"] == [
        "D07"
    ]
    assert c["counts"]["steps"] == len(c["steps"]) == 52
    accepted = {x for s in c["steps"] for x in s["accepted"]}
    decided = {
        d["control"] for d in c["decisions"] if d["route"] in ("recommended", "review")
    }
    assert decided <= accepted


def test_flagship_story(experience, cases):
    assert experience["flagship"] == "CHG-027"
    c = cases["CHG-027"]
    assert c["counts"]["check_found"] == 0
    assert c["counts"]["agent_recommended"] == c["counts"]["affected"] == 20
    assert c["counts"]["agent_recommended_right"] == 20
    # The evidence a client opens first is quoted in full phrases.
    c02 = next(d for d in c["decisions"] if d["control"] == "C02")
    assert c02["route"] == "recommended"
    assert len(c02["ticket_quote"].split()) >= 3
    assert len(c02["control_quote"].split()) >= 3


def test_earlier_approaches_match_results_doc(experience):
    doc = (ROOT / "docs" / "results.md").read_text()
    rows = {a["approach"]: a for a in experience["approaches"]}
    assert "49.5% key-miss recovery" in doc and "57.6% key-miss recovery" in doc
    assert rows["Phase 1: hybrid retrieval and ranking"]["recovery"] == 0.495
    assert rows["Phase 2: dependency-edge proposals"]["recovery"] == 0.576
    p = experience["portfolio"]
    assert (
        rows["Agent investigation (this run)"]["recovery"]
        == p["agent_found_key"] / p["key_misses"]
    )
