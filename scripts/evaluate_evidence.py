"""Evaluate two-stage evidence verification on the frozen benchmark."""
from __future__ import annotations
import argparse, json
from scripts.hybrid import hybrid_rank_controls_two_stage
from scripts.evaluate_baseline import _truth_by_change
from scripts.generate_benchmark import build_graph, build_changes
from scripts.generate_observable import build_condition


def evaluate_evidence(llm, level=30, mode="correlated", split="development",
                       runs=1, top_k=30, max_cases=None, progress=False,
                       min_confidence=0.0, cap=None, uncertain_cap=None,
                       evidence_mode="both"):
    graph = build_graph(); changes = build_changes(); truth = _truth_by_change(graph, changes)
    obs = build_condition(graph, changes, level, mode)
    selected = [c for c in obs["cases"] if c["split"] == split]
    if max_cases is not None:
        selected = selected[:max_cases]
    run_results = []
    for run in range(runs):
        total_key = base_key = final_key = total_aff = final_aff = base_work = final_work = 0
        uncertain_count = excluded_key_misses = false_positives = 0
        decisions = {}; parse_failures = []; all_audit_rows = []
        for idx, case in enumerate(selected, 1):
            if progress:
                print(f"[run {run+1}/{runs}] case {idx}/{len(selected)}: {case['change_id']}", flush=True)
            out = hybrid_rank_controls_two_stage(case, llm, top_k,
                                                   min_confidence=min_confidence,
                                                   cap=cap, uncertain_cap=uncertain_cap,
                                                   evidence_mode=evidence_mode)
            base = {x["control_id"] for x in out["baseline"]}
            recommended = set(out["recommended_control_ids"])
            uncertain = set(out.get("uncertain_control_ids", []))
            final = recommended | uncertain
            if out.get("parse_error") or out.get("stage2_parse_error"):
                parse_failures.append({
                    "change_id": case["change_id"],
                    "stage1_error": out.get("parse_error"),
                    "stage2_error": out.get("stage2_parse_error"),
                })
            labels = truth[case["change_id"]]
            aff = {cid for cid, x in labels.items() if x.affected}
            key = {cid for cid, x in labels.items() if x.affected and x.criticality == "KEY"}
            total_key += len(key); base_key += len(key & base); final_key += len(key & final)
            total_aff += len(aff); final_aff += len(aff & final); base_work += len(base); final_work += len(final)
            uncertain_count += len(uncertain)
            excluded_key_misses += len(key - final)
            false_positives += len(final - aff)
            decisions[case["change_id"]] = sorted(final)
            for row in out.get("audit_rows", []):
                row["change_id"] = case["change_id"]
                all_audit_rows.append(row)
        misses = total_key - base_key; recovered = final_key - base_key
        run_results.append({
            "run": run + 1, "key_control_pairs": total_key,
            "baseline_key_hits": base_key, "final_key_hits": final_key,
            "baseline_key_misses": misses, "recovered_key_misses": recovered,
            "key_miss_recovery_rate": 0 if not misses else recovered / misses,
            "final_key_recall": 1 if not total_key else final_key / total_key,
            "final_affected_recall": 1 if not total_aff else final_aff / total_aff,
            "baseline_workload": base_work, "final_workload": final_work,
            "workload_increase_rate": 0 if not base_work else (final_work - base_work) / base_work,
            "parse_failure_count": len(parse_failures), "parse_failures": parse_failures,
            "decisions": decisions,
            "uncertain_count": uncertain_count,
            "excluded_key_misses": excluded_key_misses,
            "false_positives": false_positives,
            "audit_rows": all_audit_rows,
        })
    agreement = 1.0
    if runs > 1:
        pairs = []
        key_ids = [n["id"] for n in graph["nodes"] if n["type"] == "CONTROL" and n.get("criticality") == "KEY"]
        for case in selected:
            for cid in key_ids:
                vals = [cid in r["decisions"][case["change_id"]] for r in run_results]
                pairs.append(1.0 if all(v == vals[0] for v in vals) else 0.0)
        agreement = sum(pairs) / len(pairs) if pairs else 1.0
    return {"level": level, "mode": mode, "split": split, "cases": len(selected),
            "runs": runs, "top_k": top_k, "two_stage": True, "evidence_mode": evidence_mode,
            "min_confidence": min_confidence, "cap": cap, "uncertain_cap": uncertain_cap,
            "key_prediction_exact_agreement": agreement,
            "repeated_run_agreement": agreement, "runs_detail": run_results}


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--model", default="databricks-llama-4-maverick")
    p.add_argument("--runs", type=int, default=1)
    p.add_argument("--top-k", type=int, default=30)
    p.add_argument("--split", choices=["development", "test"], default="development")
    p.add_argument("--level", type=int, choices=[0, 30, 60], default=30)
    p.add_argument("--mode", choices=["random", "correlated"], default="correlated")
    p.add_argument("--max-cases", type=int)
    p.add_argument("--min-confidence", type=float, default=0.0)
    p.add_argument("--cap", type=int, default=None)
    p.add_argument("--uncertain-cap", type=int, default=None)
    p.add_argument("--evidence-mode", choices=["both", "uncertain_only"], default="both")
    a = p.parse_args()
    from scripts.databricks_llm import DatabricksChatLLM
    result = evaluate_evidence(DatabricksChatLLM(a.model), level=a.level, mode=a.mode,
                                split=a.split, runs=a.runs, top_k=a.top_k,
                                max_cases=a.max_cases, progress=True,
                                min_confidence=a.min_confidence, cap=a.cap,
                                uncertain_cap=a.uncertain_cap,
                                evidence_mode=a.evidence_mode)
    # Strip large fields for console output
    for r in result["runs_detail"]:
        r.pop("audit_rows", None)
        r.pop("decisions", None)
        r.pop("parse_failures", None)
    print(json.dumps(result, indent=2))