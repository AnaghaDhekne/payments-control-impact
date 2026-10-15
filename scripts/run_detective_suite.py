"""Run the detective over development cases and score against the frozen contract.

Ground truth is computed here, offline, and is never passed to the agent: each
case is reduced to its observable payload before investigate() sees it.

Example (Databricks notebook or terminal with workspace auth):

    python -m scripts.run_detective_suite --model databricks-gpt-oss-120b \
        --max-cases 3 --max-steps 60 --output-dir output/runs/detective-suite-01

Start with --max-cases 1 or 3, read the per-case trace, then widen.
Use --runs 5 only once a single run looks sane (it multiplies cost).
"""

import argparse
import json
import time
from pathlib import Path

from scripts.case_io import observable_payload
from scripts.detective import investigate
from scripts.evaluate_baseline import _truth_by_change
from scripts.generate_benchmark import build_graph, build_changes
from scripts.generate_observable import build_condition
from scripts.score_detective import score


class _AlreadyDone(Exception):
    """Internal signal: a resumed case already has a complete saved result."""


def labels_for(truth_for_change):
    """Offline labels in the shape score_detective expects."""
    affected = sorted(k for k, v in truth_for_change.items() if v.affected)
    key = sorted(
        k for k, v in truth_for_change.items() if v.affected and v.criticality == "KEY"
    )
    return {"affected_control_ids": affected, "key_control_ids": key}


def aggregate(case_metrics):
    """Pool counts across cases (micro-averages), matching the evaluation contract."""
    misses = sum(m["key_misses"] for m in case_metrics)
    recovered = sum(m["key_recovered"] for m in case_metrics)
    new_true = sum(m["new_true_controls"] for m in case_metrics)
    new_false = sum(m["new_false_controls"] for m in case_metrics)
    base_work = sum(m["baseline_controls"] for m in case_metrics)
    extra_work = sum(m["review_items"] for m in case_metrics)
    avoidable = sum(m.get("avoidable_review_items", 0) for m in case_metrics)
    return {
        "cases": len(case_metrics),
        "key_misses": misses,
        "key_recovered": recovered,
        "key_miss_recovery": recovered / misses if misses else None,
        "target_key_miss_recovery": 0.50,
        "new_control_precision": (
            new_true / (new_true + new_false) if new_true + new_false else None
        ),
        "baseline_workload": base_work,
        "added_review_items": extra_work,
        "added_workload_vs_baseline": extra_work / base_work if base_work else None,
        "target_added_workload_max": 0.25,
        "avoidable_review_items": avoidable,
        "avoidable_review_items_per_case": (
            avoidable / len(case_metrics) if case_metrics else None
        ),
        "review_queue_true_share": (
            (extra_work - avoidable) / extra_work if extra_work else None
        ),
        "uncertain_controls": sum(m["uncertain_controls"] for m in case_metrics),
        "uninvestigated_controls": sum(
            m["uninvestigated_controls"] for m in case_metrics
        ),
        "model_calls": sum(m["model_calls"] for m in case_metrics),
        "statuses": sorted({m["status"] for m in case_metrics}),
        "note": "Development split only; prompts may have been tuned on these cases. "
        "Not a held-out result.",
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", default="databricks-gpt-oss-120b")
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--max-steps", type=int, default=60)
    parser.add_argument("--max-cases", type=int, default=None)
    parser.add_argument("--change-ids", nargs="*", help="Run only these change IDs")
    parser.add_argument("--runs", type=int, default=1)
    parser.add_argument("--level", type=int, choices=[0, 30, 60], default=30)
    parser.add_argument(
        "--mode", choices=["random", "correlated"], default="correlated"
    )
    parser.add_argument("--max-tokens", type=int, default=8000)
    parser.add_argument(
        "--resume",
        action="store_true",
        help="Continue interrupted cases from their saved result files; "
        "cases already scored are skipped",
    )
    args = parser.parse_args()

    from scripts.databricks_llm import DatabricksChatLLM

    llm = DatabricksChatLLM(args.model, max_tokens=args.max_tokens)
    graph, changes = build_graph(), build_changes()
    truth = _truth_by_change(graph, changes)
    cases = [
        c
        for c in build_condition(graph, changes, args.level, args.mode)["cases"]
        if c["split"] == "development"
    ]
    if args.change_ids:
        wanted = set(args.change_ids)
        cases = [c for c in cases if c["change_id"] in wanted]
    if args.max_cases is not None:
        cases = cases[: args.max_cases]

    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    runs = []
    for run in range(args.runs):
        case_metrics, decisions = [], {}
        for i, case in enumerate(cases, 1):
            cid = case["change_id"]
            print(f"[run {run + 1}/{args.runs}] {i}/{len(cases)} {cid}", flush=True)
            path = out_dir / f"run{run + 1}" / f"{cid}.json"
            path.parent.mkdir(parents=True, exist_ok=True)
            calls = []

            def tracked(prompt):
                response = llm(prompt)
                calls.append({"prompt": prompt, "response": response})
                return response

            def persist(state):
                path.write_text(json.dumps(state, indent=2, default=str) + "\n")

            started = time.time()
            try:
                saved = None
                if args.resume and path.exists():
                    saved = json.loads(path.read_text())
                    if "coverage" in saved and saved.get("status") != "MODEL_ERROR":
                        print(f"  {cid} already complete; rescoring saved result")
                        result = saved
                        raise _AlreadyDone
                    print(
                        f"  resuming {cid} from step "
                        f"{sum(1 for e in saved.get('trace', []) if e.get('phase') == 'investigate')}",
                        flush=True,
                    )
                result = investigate(
                    observable_payload(case),
                    tracked,
                    max_steps=args.max_steps,
                    persist=persist,
                    resume=saved,
                )
            except _AlreadyDone:
                pass
            except Exception as exc:  # keep going; the failure is recorded
                print(
                    f"  model error on {cid}: {type(exc).__name__}: {exc}", flush=True
                )
                case_metrics.append(
                    {
                        "change_id": cid,
                        "status": "MODEL_ERROR",
                        "key_misses": 0,
                        "key_recovered": 0,
                        "new_true_controls": 0,
                        "new_false_controls": 0,
                        "baseline_controls": 0,
                        "review_items": 0,
                        "uncertain_controls": 0,
                        "uninvestigated_controls": 0,
                        "avoidable_review_items": 0,
                        "model_calls": len(calls),
                    }
                )
                continue
            if calls:  # never overwrite an earlier log with an empty one
                calls_path = path.with_suffix(
                    ".resume.calls.json" if saved is not None else ".calls.json"
                )
                calls_path.write_text(json.dumps(calls, indent=2, default=str) + "\n")
            labels = labels_for(truth[cid])
            m = score(result, labels)
            m.update(
                change_id=cid,
                status=result["status"],
                baseline_controls=len(result["baseline"]),
                seconds=round(time.time() - started, 1),
                step_errors=sum(
                    1
                    for e in result["trace"]
                    if e.get("phase") == "investigate" and "error" in e
                ),
            )
            case_metrics.append(m)
            key = set(labels["key_control_ids"])
            decisions[cid] = {
                k: ("REC" if k in result["recommended_control_ids"] else "NOT")
                for k in key
            }
            print(
                f"  key misses {m['key_misses']}, recovered {m['key_recovered']}, "
                f"new true {m['new_true_controls']}, new false {m['new_false_controls']}, "
                f"uncertain {m['uncertain_controls']}, step errors {m['step_errors']}, "
                f"status {m['status']}",
                flush=True,
            )
        runs.append(
            {
                "cases": case_metrics,
                "summary": aggregate(case_metrics),
                "key_decisions": decisions,
            }
        )
        (out_dir / f"run{run + 1}" / "metrics.json").write_text(
            json.dumps(runs[-1], indent=2) + "\n"
        )
        print(json.dumps(runs[-1]["summary"], indent=2), flush=True)

    if len(runs) > 1:
        # Consistency: same key-control decision across all runs.
        pairs = agree = 0
        for cid in runs[0]["key_decisions"]:
            for ctrl in runs[0]["key_decisions"][cid]:
                vals = {r["key_decisions"].get(cid, {}).get(ctrl) for r in runs}
                pairs += 1
                agree += len(vals) == 1
        consistency = {
            "key_pairs": pairs,
            "agreement": agree / pairs if pairs else None,
            "target": 0.95,
        }
        (out_dir / "consistency.json").write_text(
            json.dumps(consistency, indent=2) + "\n"
        )
        print(json.dumps(consistency, indent=2))


if __name__ == "__main__":
    main()
