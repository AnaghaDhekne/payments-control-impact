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
    # The first early finish is answered with a reminder; the second is honoured.
    result, _ = run(cmds + [{"action": "finish"}])
    assert result["findings"] == []
    assert result["uninvestigated_control_ids"] == ["C-ADDRESS"]
    assert "fabricated" in result["trace"][2]["error"]
    assert "not_finished" in result["trace"][3]["result"]
    assert result["status"] == "FINISHED"


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


# --- Agentic-path regressions -------------------------------------------------


def test_reasoning_model_block_content_is_parsed():
    """gpt-oss on Databricks returns [reasoning, text] blocks, not a string."""
    from scripts.databricks_llm import content_text

    blocks = [
        {"type": "reasoning", "summary": [{"type": "summary_text", "text": "{bad}"}]},
        {"type": "text", "text": '{"action": "finish"}'},
    ]
    assert content_text(blocks) == '{"action": "finish"}'
    assert content_text(json.dumps(blocks)) == '{"action": "finish"}'
    assert content_text("plain") == "plain"
    assert content_text(None) == ""

    responses = iter(
        [
            {"action": "inspect_control", "args": {"control_id": "C-ADDRESS"}},
            {"action": "submit_finding", "args": finding()},
            {"action": "finish"},
            finding(),
        ]
    )

    def gptoss(prompt):
        return [
            {"type": "reasoning", "summary": []},
            {"type": "text", "text": json.dumps(next(responses))},
        ]

    result = investigate(demo()["case"], gptoss, max_steps=5)
    assert all("error" not in e for e in result["trace"])
    assert result["recommended_control_ids"] == ["C-ADDRESS"]


def test_batch_inspect_and_submit():
    result, _ = run(
        [
            {"action": "inspect_control", "args": {"control_ids": ["C-ADDRESS"]}},
            {"action": "submit_findings", "args": {"findings": [finding()]}},
            {"action": "finish"},
            finding(),
        ]
    )
    assert result["recommended_control_ids"] == ["C-ADDRESS"]
    assert result["trace"][1]["result"]["accepted_for_verification"] == ["C-ADDRESS"]


def test_batch_submit_reports_rejections_without_dropping_valid_findings():
    bad = dict(finding(), control_quote="Invented quotation")
    result, _ = run(
        [
            {"action": "inspect_control", "args": {"control_ids": ["C-ADDRESS"]}},
            {"action": "submit_findings", "args": {"findings": [bad]}},
            {"action": "submit_findings", "args": {"findings": [finding()]}},
            {"action": "finish"},
            finding(),
        ]
    )
    assert "fabricated" in result["trace"][1]["result"]["rejected"][0]["error"]
    assert result["recommended_control_ids"] == ["C-ADDRESS"]


def test_explore_node_reports_visible_edges():
    case = demo()["case"]
    tools = EvidenceTools(case)
    nid = case["change_ticket"]["changed_entity_ids"][0]
    out = tools.call("explore_node", {"node_id": nid})
    assert out["node"]["id"] == nid
    assert "outgoing" in out and "incoming" in out
    with pytest.raises(ValueError):
        tools.call("explore_node", {"node_id": "NOPE"})


def test_evidence_path_must_use_known_nodes():
    bad = dict(finding(), evidence_path=["NOT-A-NODE"])
    result, _ = run(
        [
            {"action": "inspect_control", "args": {"control_id": "C-ADDRESS"}},
            {"action": "submit_finding", "args": bad},
            {"action": "finish"},
            {"action": "finish"},
        ]
    )
    assert result["findings"] == []
    assert "evidence_path" in result["trace"][1]["error"]


def test_verifier_retries_once_after_invalid_output():
    result, _ = run(commands() + [{"decision": "AFFECTED"}, finding()])
    assert result["recommended_control_ids"] == ["C-ADDRESS"]


def test_prompt_does_not_resend_old_tool_output_in_full():
    case = demo()["case"]
    cmds = [{"action": "search_controls", "args": {"query": "address"}}] * 5 + [
        {"action": "finish"},
        {"action": "finish"},
    ]
    _, prompts = run(cmds, case, max_steps=8)
    # Prompt growth stays bounded: only the latest observations are in full.
    assert len(prompts[5]) - len(prompts[3]) < len(prompts[3]) // 2


def test_reasoning_only_reply_falls_back_to_json_in_reasoning():
    """gpt-oss sometimes stops with only a reasoning block and no answer block."""
    from scripts.databricks_llm import content_text

    blocks = [
        {
            "type": "reasoning",
            "summary": [
                {
                    "type": "summary_text",
                    "text": 'Start at D03. {"action": "explore_node", "args": {"node_id": "D03"}}',
                }
            ],
        }
    ]
    assert json.loads(content_text(blocks)) == {
        "action": "explore_node",
        "args": {"node_id": "D03"},
    }
    assert content_text([{"type": "reasoning", "summary": []}]) == ""
    # An answer block always wins over reasoning.
    blocks.append({"type": "text", "text": '{"action": "finish"}'})
    assert content_text(blocks) == '{"action": "finish"}'


def test_tool_and_arguments_spelling_is_accepted():
    """gpt-oss often writes {"tool": ..., "arguments": ...} instead of {action, args}."""
    from scripts.detective import parse_command

    assert parse_command({"tool": "trace_metadata", "arguments": {}}) == (
        "trace_metadata",
        {},
    )
    assert parse_command(
        {"function": {"name": "explore_node", "arguments": '{"node_id": "D03"}'}}
    ) == ("explore_node", {"node_id": "D03"})
    assert (
        parse_command({"action": "inspect_controls", "args": {"control_ids": ["A"]}})[0]
        == "inspect_control"
    )
    with pytest.raises(ValueError, match="Missing action"):
        parse_command({"foo": 1})
    result, _ = run(
        [
            {"tool": "inspect_control", "arguments": {"control_id": "C-ADDRESS"}},
            {"tool": "submit_finding", "arguments": finding()},
            {"tool": "finish"},
            finding(),
        ]
    )
    assert all("error" not in e for e in result["trace"])
    assert result["recommended_control_ids"] == ["C-ADDRESS"]


def test_batch_inspect_keeps_valid_ids_and_reports_unknown():
    tools = EvidenceTools(demo()["case"])
    out = tools.call("inspect_control", {"control_ids": ["C-ADDRESS", "C999"]})
    assert out[0]["document"]["control_id"] == "C-ADDRESS"
    assert out[-1]["unknown_control_ids"] == ["C999"]
    assert "C-ADDRESS" in tools.inspected
    with pytest.raises(ValueError):
        tools.call("inspect_control", {"control_ids": ["C999"]})


def test_unknown_tool_error_lists_valid_tools():
    result, _ = run(
        [{"action": "lookup", "args": {}}, {"action": "finish"}, {"action": "finish"}],
        max_steps=3,
    )
    assert "inspect_control" in result["trace"][0]["error"]
