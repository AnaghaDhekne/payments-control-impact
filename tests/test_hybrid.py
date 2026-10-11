import json
from scripts.hybrid import (
    retrieve_control_documents,
    parse_recommendations,
    hybrid_rank_controls,
)
from scripts.generate_benchmark import build_graph, build_changes
from scripts.generate_observable import build_condition


def sample_case():
    return build_condition(build_graph(), build_changes(), 30, "correlated")["cases"][0]


def test_retrieval_is_deterministic_and_bounded():
    c = sample_case()
    a = retrieve_control_documents(c, 12)
    b = retrieve_control_documents(c, 12)
    assert a == b and len(a) == 12
    assert all("affected" not in d and "actions" not in d for d in a)


def test_parser_rejects_unknown_control_ids():
    raw = json.dumps(
        {
            "recommendations": [
                {
                    "control_id": "C9999",
                    "decision": "AFFECTED",
                    "actions": ["REASSESS_DESIGN"],
                    "confidence": 0.9,
                    "reason": "x",
                },
                {
                    "control_id": "C01",
                    "decision": "UNCERTAIN",
                    "actions": ["BAD", "REFRESH_EVIDENCE"],
                    "confidence": 0.5,
                    "reason": "y",
                },
            ]
        }
    )
    out = parse_recommendations(raw, {"C01"})
    assert [x["control_id"] for x in out] == ["C01"]
    assert out[0]["actions"] == ["REFRESH_EVIDENCE"]


def test_hybrid_preserves_baseline_and_adds_recovery():
    c = sample_case()
    chosen = retrieve_control_documents(c, 20)[0]["control_id"]

    def fake_llm(_):
        return json.dumps(
            {
                "recommendations": [
                    {
                        "control_id": chosen,
                        "decision": "AFFECTED",
                        "actions": ["REASSESS_DESIGN"],
                        "confidence": 0.8,
                        "reason": "narrative dependency",
                    }
                ]
            }
        )

    out = hybrid_rank_controls(c, fake_llm, 20)
    baseline = {x["control_id"] for x in out["baseline"]}
    assert baseline <= set(out["recommended_control_ids"])
    assert chosen in out["recommended_control_ids"]
