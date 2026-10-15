"""Check tool execution, evidence boundaries, uncertainty, and offline scoring."""

import json
from copy import deepcopy
import pytest
from scripts.detective import investigate, EvidenceTools
from tests.fixtures import demo_case
from scripts.score_detective import score


def run(responses, case=None, max_steps=6):
    prompts = []
    iterator = iter(responses)

    def llm(prompt):
        prompts.append(prompt)
        return json.dumps(next(iterator))

    case = case or demo_case()
    original = deepcopy(case)
    result = investigate(case, llm, max_steps=max_steps)
    assert case == original
    return result, prompts


def finding(decision="AFFECTED"):
    return {
        "control_id": "C-ADDRESS",
        "decision": decision,
        "ticket_quote": "Update structured address validation rule.",
        "control_quote": demo_case()["control_documents"][0]["text"],
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
    # An early finish is answered with a reminder while more than 3 steps remain.
    result, _ = run(cmds + [{"action": "finish"}], max_steps=7)
    assert result["findings"] == []
    assert result["uninvestigated_control_ids"] == ["C-ADDRESS"]
    assert "fabricated" in result["trace"][2]["error"]
    assert "not_finished" in result["trace"][3]["result"]
    assert result["status"] == "FINISHED"


def test_labels_excluded_from_all_model_calls():
    case = demo_case()
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
    tools = EvidenceTools(demo_case())
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
            demo_case(),
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

    result = investigate(demo_case(), gptoss, max_steps=5)
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
    case = demo_case()
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
    case = demo_case()
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
    tools = EvidenceTools(demo_case())
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


def test_verifier_sees_family_and_change_neighborhood():
    """The verifier needs sibling-control and downstream evidence for indirect impact."""
    from scripts.detective import verification_evidence, control_family

    case = deepcopy(demo_case())
    base = case["control_documents"][0]
    base["title"] = "Address validation — daily"
    sib = dict(base, control_id="C-SIB", title="Address validation — manual")
    case["control_documents"].append(sib)
    tools = EvidenceTools(case)
    family, siblings = control_family(tools, base["control_id"])
    assert family == "Address validation" and siblings == ["C-SIB"]
    ev = verification_evidence(
        tools, tools.case["change_ticket"], {"control_id": base["control_id"]}
    )
    assert ev["control_family"]["members"][0]["control_id"] == "C-SIB"
    assert "change_neighborhood" in ev and "hypothesis" in ev
    assert "ground_truth" not in json.dumps(ev)


def test_cut_off_submission_recovers_complete_findings():
    """A reply truncated at the output limit keeps every complete finding."""
    full = json.dumps({"action": "submit_findings", "args": {"findings": [finding()]}})
    cut = full[:-3] + ', {"control_id": "C-ADDR'  # truncated mid second finding
    replies = iter(
        [
            json.dumps(
                {"action": "inspect_control", "args": {"control_id": "C-ADDRESS"}}
            ),
            cut,
            json.dumps({"action": "finish"}),
            json.dumps(finding()),
        ]
    )
    result = investigate(demo_case(), lambda p: next(replies), max_steps=3)
    assert result["trace"][1]["result"]["accepted_for_verification"] == ["C-ADDRESS"]
    assert "cut off" in result["trace"][1]["result"]["note"]
    assert result["recommended_control_ids"] == ["C-ADDRESS"]


def test_oversized_batch_processes_first_eight():
    from scripts.detective import MAX_SUBMIT_BATCH

    result, _ = run(
        [
            {"action": "inspect_control", "args": {"control_id": "C-ADDRESS"}},
            {
                "action": "submit_findings",
                "args": {"findings": [finding()] * (MAX_SUBMIT_BATCH + 2)},
            },
            {"action": "finish"},
            finding(),
        ],
        max_steps=3,
    )
    out = result["trace"][1]["result"]
    assert len(out["not_processed_over_batch_limit"]) == 2
    assert result["recommended_control_ids"] == ["C-ADDRESS"]


def test_unaffected_is_recorded_without_verifier_call():
    prompts_seen = []
    result, prompts_seen = run(
        [
            {"action": "inspect_control", "args": {"control_id": "C-ADDRESS"}},
            {"action": "submit_finding", "args": finding("UNAFFECTED")},
            {"action": "finish"},
        ],
        max_steps=3,
    )
    assert len(prompts_seen) == 3  # no verification call
    assert result["recommended_control_ids"] == []
    assert result["uncertain_control_ids"] == []
    assert result["verified_findings"][0]["verification_reason"].startswith(
        "Not verified"
    )


def test_verifier_missing_counter_evidence_is_tolerated():
    reply = dict(finding())
    reply.pop("counter_evidence")
    result, _ = run(commands() + [reply])
    assert result["recommended_control_ids"] == ["C-ADDRESS"]


def test_reasoning_fallback_ignores_empty_fragments():
    from scripts.databricks_llm import content_text

    text = 'Call trace_metadata {} first. Then {"action": "trace_metadata", "args": {}}. Use args {}.'
    blocks = [
        {"type": "reasoning", "summary": [{"type": "summary_text", "text": text}]}
    ]
    assert json.loads(content_text(blocks)) == {"action": "trace_metadata", "args": {}}
    only_fragments = [
        {
            "type": "reasoning",
            "summary": [{"type": "summary_text", "text": "use {} and {}"}],
        }
    ]
    assert content_text(only_fragments) == ""


def test_resume_continues_from_saved_state():
    """An interrupted run resumes with its findings and memory, not from scratch."""
    snapshots = []
    first = iter(
        [
            {"action": "inspect_control", "args": {"control_id": "C-ADDRESS"}},
            {"action": "submit_finding", "args": finding()},
        ]
    )

    def dies(prompt):
        try:
            return json.dumps(next(first))
        except StopIteration:
            raise RuntimeError("terminal closed")

    with pytest.raises(RuntimeError):
        investigate(
            demo_case(),
            dies,
            max_steps=6,
            persist=lambda s: snapshots.append(json.loads(json.dumps(s))),
        )
    saved = snapshots[-1]
    assert saved["status"] == "MODEL_ERROR" and len(saved["findings"]) == 1

    prompts = []
    rest = iter([{"action": "finish"}, finding()])

    def llm(prompt):
        prompts.append(prompt)
        return json.dumps(next(rest))

    result = investigate(demo_case(), llm, max_steps=6, resume=saved)
    assert result["resumed_from_step"] == 3  # two good steps + the failed one
    assert result["recommended_control_ids"] == ["C-ADDRESS"]
    assert "C-ADDRESS" in prompts[0]  # restored notebook is in the prompt
    with pytest.raises(ValueError):
        other = deepcopy(demo_case())
        other["change_ticket"]["text"] += " changed"
        investigate(other, llm, max_steps=6, resume=saved)


def test_resume_after_investigation_finished_only_reverifies():
    snapshots = []
    replies = iter(commands())

    def llm(prompt):
        return json.dumps(next(replies))

    # Investigation finishes; the verification call then fails (-> UNCERTAIN).
    investigate(
        demo_case(),
        llm,
        max_steps=6,
        persist=lambda s: snapshots.append(json.loads(json.dumps(s))),
    )
    # The snapshot taken right after "finish", before any verification.
    saved = next(
        s
        for s in snapshots
        if s["status"] == "FINISHED" and "verified_findings" not in s
    )
    calls = []
    result = investigate(
        demo_case(),
        lambda p: calls.append(p) or json.dumps(finding()),
        max_steps=6,
        resume=saved,
    )
    assert len(calls) == 1  # only the verification call
    assert result["recommended_control_ids"] == ["C-ADDRESS"]


def test_resume_keeps_completed_verifications():
    snapshots = []
    replies = iter(commands() + [finding()])
    investigate(
        demo_case(),
        lambda p: json.dumps(next(replies)),
        max_steps=6,
        persist=lambda s: snapshots.append(json.loads(json.dumps(s))),
    )
    saved = snapshots[-1]
    calls = []
    result = investigate(
        demo_case(), lambda p: calls.append(p) or "{}", max_steps=6, resume=saved
    )
    assert calls == []  # nothing re-asked
    assert result["recommended_control_ids"] == ["C-ADDRESS"]


def test_score_reports_review_burden_measures():
    result = {
        "baseline": [{"control_id": "B"}],
        "recommended_control_ids": ["B", "T1", "F1"],
        "uncertain_control_ids": ["T2", "F2"],
        "uninvestigated_control_ids": [],
        "trace": [],
    }
    labels = {"affected_control_ids": ["B", "T1", "T2"], "key_control_ids": ["T1"]}
    m = score(result, labels)
    assert m["review_items"] == 4
    assert m["avoidable_review_items"] == 2  # F1, F2
    assert m["review_queue_true_share"] == 0.5
    assert m["uncertain_true_controls"] == 1
