"""File-based proposal/review workflow and offline wiring demonstration."""

import argparse
import json
from pathlib import Path
from scripts.dependency_proposals import propose, validate_proposals, apply_reviews


def demo():
    """Run a hand-authored wiring fixture with simulated approval, not a live evaluation."""
    case = {
        "change_id": "DEMO-ADDRESS",
        "change_ticket": {
            "title": "Structured address validation update",
            "text": "Update structured address validation rule.",
            "changed_entity_ids": ["R-ADDRESS"],
        },
        "visible_metadata": {
            "nodes": [
                {
                    "id": "R-ADDRESS",
                    "name": "Structured address validation rule",
                    "type": "RULE",
                },
                {
                    "id": "C-ADDRESS",
                    "name": "Address validation control",
                    "type": "CONTROL",
                    "criticality": "KEY",
                },
            ],
            "edges": [],
        },
        "control_documents": [
            {
                "control_id": "C-ADDRESS",
                "title": "Address validation",
                "text": "The address validation control depends directly on the structured address validation rule.",
            }
        ],
    }
    # Hand-authored fixture: NOT a model result and NOT benchmark evidence.
    fixture = {
        "source": "R-ADDRESS",
        "target": "C-ADDRESS",
        "relationship": "DEPENDS_ON",
        "ticket_quote": "Update structured address validation rule.",
        "control_quote": case["control_documents"][0]["text"],
        "reason": "The control document states this direct dependency.",
    }
    batch = validate_proposals(case, json.dumps({"proposals": [fixture]}))
    review = {
        "proposal_id": batch["proposals"][0]["proposal_id"],
        "decision": "APPROVE",
        "reviewer": "SIMULATED-DEMO-REVIEWER",
        "reviewed_at": "2026-10-11T00:00:00Z",
        "reason": "Fixture document explicitly states direct dependency.",
    }
    return {
        "status": "OFFLINE FIXTURE ONLY — no live LLM or real human review",
        "case": case,
        "batch": batch,
        "result": apply_reviews(case, batch, [review]),
    }


def main():
    """Dispatch demo, proposal generation, or explicit review from JSON files."""
    p = argparse.ArgumentParser()
    p.add_argument("mode", choices=["demo", "propose", "review"])
    p.add_argument("--case")
    p.add_argument("--batch")
    p.add_argument("--reviews")
    p.add_argument(
        "--response", help="Saved raw model response; omit to call Databricks"
    )
    p.add_argument("--model", default="databricks-llama-4-maverick")
    p.add_argument("--output", required=True)
    a = p.parse_args()
    read = lambda path: json.loads(Path(path).read_text())
    if a.mode == "demo":
        result = demo()
    elif a.mode == "propose":
        case = read(a.case)
        if a.response:
            result = validate_proposals(case, Path(a.response).read_text())
        else:
            from scripts.databricks_llm import DatabricksChatLLM

            result = propose(case, DatabricksChatLLM(a.model))
        result["model"] = a.model
    else:
        result = apply_reviews(read(a.case), read(a.batch), read(a.reviews))
    Path(a.output).parent.mkdir(parents=True, exist_ok=True)
    Path(a.output).write_text(json.dumps(result, indent=2) + "\n")


if __name__ == "__main__":
    main()
