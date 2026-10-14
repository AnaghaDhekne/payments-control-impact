"""Check tool execution, evidence boundaries, uncertainty, and offline scoring."""

import json
from copy import deepcopy
import pytest
from scripts.detective import investigate, EvidenceTools
from scripts.run_dependency_review import demo
from scripts.score_detective import score


def run(responses, case=None, max_steps=6):
    prompts = []
    iterator = iter(responses)

    def llm(prompt):
        prompts.append(prompt)
        return json.dumps(next(iterator))

    case = case or demo()["case"]
    original = deepcopy(case)
    result = investigate(case, llm, max_steps=max_steps)
    assert case == original
    return result, prompts


def finding(decision="AFFECTED"):
    return {
        "control_id": "C-ADDRESS",
        "decision": decision,
        "ticket_quote": "Update structured address validation rule.",
        "control_quote": demo()["case"]["control_documents"][0]["text"],
        "causal_reason": "Changing the validation rule changes the behavior used by the address control.",
        "counter_evidence": "No exclusion is stated in this fixture.",
    }


def commands():
    return [
        {"action": "search_controls", "args": {"query": "structured address"}},
        {"action": "inspect_control", "args": {"control_id": "C-ADDRESS"}},
        {"action": "submit_finding", "args": finding()},
        {"action": "finish"},
    ]


def test_tool_loop_verifies_impact_without_mutating_graph():
    result, prompts = run(commands() + [finding()])
    assert result["recommended_control_ids"] == ["C-ADDRESS"]
    assert result["coverage"]["verified"] == 1
    assert result["uninvestigated_control_ids"] == []
    assert "document" in prompts[2]
    assert result["trace"][-1]["phase"] == "verify"


def test_verifier_disagreement_is_uncertain_and_not_recovered():
    result, _ = run(commands() + [finding("UNAFFECTED")])
    assert result["recommended_control_ids"] == []
    assert result["uncertain_control_ids"] == ["C-ADDRESS"]
    metrics = score(
        result,
        {"affected_control_ids": ["C-ADDRESS"], "key_control_ids": ["C-ADDRESS"]},
    )
    assert metrics["key_miss_recovery"] == 0
    assert metrics["review_items"] == 1


def test_fabricated_quote_rejected_without_quote_correction():
    cmds = commands()
    cmds[2]["args"]["control_quote"] = "Invented quotation"
    result, _ = run(cmds)
    assert result["findings"] == []
    assert result["uninvestigated_control_ids"] == ["C-ADDRESS"]
    assert "fabricated" in result["trace"][2]["error"]


def test_labels_excluded_from_all_model_calls():
    case = demo()["case"]
    case["ground_truth"] = "SECRET-LABEL"
    case["degradation_manifest"] = {"removed_edge_ids": ["SECRET-EDGE"]}
    result, prompts = run(commands() + [finding()], case)
    assert all("SECRET" not in p for p in prompts)
    assert result["recommended_control_ids"]


def test_unknown_tools_and_budget_leave_unresolved_controls():
    result, _ = run([{"action": "delete_graph", "args": {}}], max_steps=1)
    assert result["status"] == "BUDGET_EXHAUSTED"
    assert result["uninvestigated_control_ids"] == ["C-ADDRESS"]
    assert "Unknown tool" in result["trace"][0]["error"]


def test_zero_lexical_overlap_does_not_remove_control():
    tools = EvidenceTools(demo()["case"])
    assert (
        tools.call("search_controls", {"query": "unrelated"})[0]["control_id"]
        == "C-ADDRESS"
    )
    with pytest.raises(ValueError):
        tools.call("inspect_control", {"control_id": "MISSING"})


def test_missing_verification_cannot_promote_finding():
    result, _ = run(commands() + [{"decision": "AFFECTED"}])
    assert result["recommended_control_ids"] == []
    assert result["uncertain_control_ids"] == ["C-ADDRESS"]


def test_model_error_is_checkpointed_and_raised():
    checkpoints = []

    def broken(prompt):
        raise RuntimeError("endpoint unavailable")

    with pytest.raises(RuntimeError):
        investigate(
            demo()["case"],
            broken,
            persist=lambda state: checkpoints.append(deepcopy(state)),
        )
    assert checkpoints[-1]["status"] == "MODEL_ERROR"
