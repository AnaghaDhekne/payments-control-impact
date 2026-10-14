"""Offline impact scoring. Hidden labels never enter detective prompts."""

import argparse
import json
from pathlib import Path


def score(result, labels):
    """Score control impact separately from direct-edge accuracy and review burden."""
    affected = set(labels["affected_control_ids"])
    key = set(labels["key_control_ids"]) & affected
    baseline = {r["control_id"] for r in result["baseline"]}
    recommended = set(result["recommended_control_ids"])
    new = recommended - baseline
    misses = key - baseline
    recovered = misses & new
    uncertain = set(result["uncertain_control_ids"])
    return {
        "key_misses": len(misses),
        "key_recovered": len(recovered),
        "key_miss_recovery": len(recovered) / len(misses) if misses else None,
        "new_control_precision": len(new & affected) / len(new) if new else None,
        "new_true_controls": len(new & affected),
        "new_false_controls": len(new - affected),
        "remaining_key_misses": sorted(key - recommended),
        "uncertain_controls": len(uncertain),
        "uninvestigated_controls": len(result["uninvestigated_control_ids"]),
        "review_items": len(new | uncertain),
        "model_calls": len(result["trace"]),
        "note": "UNCERTAIN counts as workload, not a recovered control. No direct edges asserted.",
    }


def main():
    """Evaluate one saved run against independently supplied labels."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--result", required=True)
    parser.add_argument("--labels", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    read = lambda p: json.loads(Path(p).read_text(encoding="utf-8"))
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(score(read(args.result), read(args.labels)), indent=2) + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
