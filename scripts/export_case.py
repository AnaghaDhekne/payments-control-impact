"""Export a development case without hidden labels or damage metadata."""

import argparse
import json
from pathlib import Path

from scripts.case_io import observable_payload
from scripts.generate_benchmark import build_graph, build_changes
from scripts.generate_observable import build_condition


def export_case(change_id: str, level: int = 30, mode: str = "correlated") -> dict:
    """Select a development scenario and expose only runtime-approved fields."""
    condition = build_condition(build_graph(), build_changes(), level, mode)
    case = next((c for c in condition["cases"] if c["change_id"] == change_id), None)
    if case is None:
        raise ValueError(f"Unknown change ID: {change_id}")
    if case["split"] != "development":
        raise ValueError("This command exports development cases only")
    return observable_payload(case)


def main():
    """Write one observable case for the file-based proposal workflow."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--change-id", required=True)
    parser.add_argument("--level", type=int, choices=[0, 30, 60], default=30)
    parser.add_argument(
        "--mode", choices=["random", "correlated"], default="correlated"
    )
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    payload = export_case(args.change_id, args.level, args.mode)
    target = Path(args.output)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
