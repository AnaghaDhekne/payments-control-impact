"""Benchmark scoring determinism and the observable-data boundary."""

import json

import pytest

from scripts.case_io import case_digest, extract_json, observable_payload
from scripts.evaluate_baseline import evaluate_condition
from scripts.generate_benchmark import build_changes, build_graph
from scripts.generate_observable import build_condition


@pytest.fixture(scope="module")
def dev_cases():
    obs = build_condition(build_graph(), build_changes(), level=30, mode="correlated")
    return [c for c in obs["cases"] if c["split"] == "development"]


class TestDeterministicScoring:
    def test_evaluate_condition_is_deterministic(self):
        assert evaluate_condition(30, "correlated", "test") == evaluate_condition(
            30, "correlated", "test"
        )

    def test_baseline_key_misses_match_expected(self):
        """Development split has 225 unreachable key-control pairs at 30% correlated."""
        r = evaluate_condition(30, "correlated", "development")
        assert r["unreachable_key_control_pairs"] == 225
        assert r["cases"] == 36

    def test_zero_degradation_full_recall(self):
        assert evaluate_condition(0, "random", "test")["key_control_recall"] == 1.0


class TestInformationBoundary:
    def test_observable_payload_excludes_hidden(self, dev_cases):
        case = dev_cases[0]
        assert "degradation_manifest" in case and "split" in case
        payload = observable_payload(case)
        assert set(payload) == {
            "change_id",
            "change_ticket",
            "visible_metadata",
            "control_documents",
        }

    def test_case_digest_ignores_evaluation_fields(self, dev_cases):
        case = dev_cases[0]
        assert case_digest(case) == case_digest(observable_payload(case))
        changed = json.loads(json.dumps(observable_payload(case)))
        changed["change_ticket"]["text"] += " edited"
        assert case_digest(changed) != case_digest(case)


def test_extract_json_handles_fences_and_prose():
    assert json.loads(extract_json('```json\n{"a": 1}\n```')) == {"a": 1}
    assert json.loads(extract_json('Answer: {"a": 2} done')) == {"a": 2}
    assert extract_json("no json") == "no json"
