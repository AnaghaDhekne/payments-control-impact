"""Offline scorer only. Truth must never be provided to the proposer or reviewer.

Input labels are case-specific lists: affected_control_ids and key_control_ids.
Review correctness uses an independently adjudicated correct_proposal_ids list.
"""

import argparse
import json
from pathlib import Path


def score(result, labels):
    """Count recovery and every reviewed proposal; null ratios mean no denominator."""
    base = {r["control_id"] for r in result["baseline"]}
    final = {r["control_id"] for r in result["final"]}
    affected = set(labels["affected_control_ids"])
    key = set(labels["key_control_ids"])
    if not key <= affected:
        raise ValueError("Affected key labels must be a subset of affected labels")
    misses = key - base
    reviewed = result["review_audit"]
    correct = set(labels["correct_proposal_ids"])
    approved = [r for r in reviewed if r["decision"] == "APPROVE"]
    recovered = len(misses & final)
    return {
        "baseline_key_misses": len(misses),
        "recovered_key_misses": recovered,
        "key_miss_recovery_rate": recovered / len(misses) if misses else None,
        "excluded_key_misses": sorted(key - final),
        "proposal_reviews": len(reviewed),
        "pending_proposals": len(result["pending_proposals"]),
        "uncertain_reviews": sum(r["decision"] == "UNCERTAIN" for r in reviewed),
        "reviewed_proposal_precision": (
            sum(r["proposal_id"] in correct for r in reviewed) / len(reviewed)
            if reviewed
            else None
        ),
        "incorrect_approved_edges": sum(
            r["proposal_id"] not in correct for r in approved
        ),
        "final_control_reviews": len(final),
        "false_positive_controls": len(final - affected),
        "total_review_items": len(reviewed) + len(final),
        "proposal_reviews_per_recovered_key": (
            len(reviewed) / recovered if recovered else None
        ),
    }


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--result", required=True)
    p.add_argument("--labels", required=True)
    p.add_argument("--output", required=True)
    a = p.parse_args()
    output = score(
        json.loads(Path(a.result).read_text()), json.loads(Path(a.labels).read_text())
    )
    Path(a.output).write_text(json.dumps(output, indent=2) + "\n")
