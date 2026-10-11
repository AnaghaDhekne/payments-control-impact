import json
from pathlib import Path

from scripts.ground_truth import Change, label_change, load_graph

ROOT = Path(__file__).resolve().parents[1]


def _affected(labels):
    return {x.control_id: set(x.actions) for x in labels if x.affected}


def test_structured_address_change_hits_validation_screening_and_mapping():
    graph = load_graph()
    change = Change("CHG-001", ("D03", "D04"), "FIELD_MAPPING", "2026-11-14")
    got = _affected(
        label_change(
            graph, change, test_period_start="2026-10-01", test_period_end="2026-12-31"
        )
    )
    assert {"C01", "C02", "C06"}.issubset(got)
    assert "REASSESS_DESIGN" in got["C01"]
    assert "REASSESS_DESIGN" in got["C02"]
    assert "OUT_OF_CYCLE_TEST" in got["C01"]
    assert "OUT_OF_CYCLE_TEST" in got["C02"]


def test_report_only_change_refreshes_evidence_not_design():
    graph = load_graph()
    change = Change("CHG-002", ("RP01",), "REPORT_CHANGE", "2026-12-01")
    got = _affected(label_change(graph, change))
    assert set(got) == {"C03"}
    assert got["C03"] == {"REFRESH_EVIDENCE"}


def test_threshold_change_reaches_key_authorization_control():
    graph = load_graph()
    change = Change("CHG-003", ("R02",), "PARAMETER_CHANGE", "2026-12-15")
    got = _affected(label_change(graph, change))
    assert "C04" in got
    assert "REASSESS_DESIGN" in got["C04"]


def test_compensating_link_does_not_auto_propagate():
    graph = load_graph()
    change = Change("CHG-X", ("C02",), "CONTROL_CHANGE", "2026-12-15")
    got = _affected(label_change(graph, change))
    assert "C11" not in got


def test_all_seed_scenarios_reference_real_nodes():
    graph = load_graph()
    ids = {n["id"] for n in graph["nodes"]}
    scenarios = json.loads(
        (ROOT / "data" / "ground_truth" / "seed_changes.json").read_text()
    )
    for s in scenarios:
        assert set(s["changed_node_ids"]) <= ids
