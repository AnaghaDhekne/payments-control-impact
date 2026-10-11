import json
import pytest
from scripts.hybrid import parse_recommendations, hybrid_rank_controls
from scripts.generate_benchmark import build_graph, build_changes
from scripts.generate_observable import build_condition


def test_fenced_array_and_named_confidence():
    raw = """```json
[
  {"control_id":"C01","decision":"AFFECTED","actions":["REASSESS_DESIGN"],"confidence":"HIGH","reason":"dependency"},
  {"control_id":"C02","decision":"UNCERTAIN","actions":[],"confidence":"MEDIUM","reason":"unclear"}
]
```"""
    out = parse_recommendations(raw, {"C01", "C02"})
    assert len(out) == 2
    assert out[0]["confidence"] == 1.0
    assert out[1]["confidence"] == 0.67


def test_fenced_object_and_numeric_confidence():
    raw = (
        "```json\n"
        + json.dumps(
            {
                "recommendations": [
                    {
                        "control_id": "C01",
                        "decision": "UNAFFECTED",
                        "actions": [],
                        "confidence": 0.8,
                        "reason": "none",
                    }
                ]
            }
        )
        + "\n```"
    )
    out = parse_recommendations(raw, {"C01"})
    assert len(out) == 1 and out[0]["confidence"] == 0.8


def test_empty_response_is_explicit_error():
    with pytest.raises(ValueError, match="empty model response"):
        parse_recommendations("", {"C01"})


def test_parse_failure_preserves_baseline_and_is_visible():
    case = build_condition(build_graph(), build_changes(), 30, "correlated")["cases"][0]
    out = hybrid_rank_controls(case, lambda _: "not json", top_k=5)
    assert out["parse_error"]
    assert out["raw_model_response"] == "not json"
    assert {x["control_id"] for x in out["baseline"]} == set(
        out["recommended_control_ids"]
    )
