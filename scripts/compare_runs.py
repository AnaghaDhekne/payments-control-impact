"""Compare two agent versions run on the same cases, run by run, against the answer key.

    python -m scripts.compare_runs --a <folder-of-A> --b <folder-of-B> --runs 1 2

Each folder holds run<N>/<case>.json. Reports, per version and pooled over
the listed runs: key-miss recovery, new-control precision, avoidable
(unaffected) review items, UNCERTAIN, undecided key controls, model calls,
and repeatability (share of affected key controls with the same recommend /
not-recommend decision in every listed run). Only cases finished in every run
of both versions are used. Labels are computed offline.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from scripts.ensemble import agreement, key_decisions, load_run
from scripts.evaluate_baseline import _truth_by_change
from scripts.generate_benchmark import build_changes, build_graph
from scripts.run_detective_suite import labels_for
from scripts.score_detective import score


def pooled(results, labels):
    keys = (
        "key_misses",
        "key_recovered",
        "new_true_controls",
        "new_false_controls",
        "avoidable_review_items",
        "uncertain_controls",
        "model_calls",
    )
    tot = dict.fromkeys(keys, 0)
    tot["undecided_key_controls"] = 0
    for r in results:
        m = score(r, labels[r["change_id"]])
        for k in keys:
            tot[k] += m[k]
        tot["undecided_key_controls"] += len(
            set(r["uninvestigated_control_ids"])
            & set(labels[r["change_id"]]["key_control_ids"])
        )
    tot["key_miss_recovery"] = (
        tot["key_recovered"] / tot["key_misses"] if tot["key_misses"] else None
    )
    nt, nf = tot["new_true_controls"], tot["new_false_controls"]
    tot["new_control_precision"] = nt / (nt + nf) if nt + nf else None
    return tot


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--a", required=True)
    p.add_argument("--b", required=True)
    p.add_argument("--runs", nargs="+", type=int, default=[1, 2])
    args = p.parse_args()
    folders = {"A": Path(args.a), "B": Path(args.b)}
    runs = {v: {n: load_run(f, n) for n in args.runs} for v, f in folders.items()}
    cases = sorted(
        set.intersection(*(set(r) for rr in runs.values() for r in rr.values()))
    )
    truth = _truth_by_change(build_graph(), build_changes())
    labels = {c: labels_for(truth[c]) for c in cases}
    out = {"cases": cases, "runs": args.runs}
    for v in folders:
        per_run = {n: pooled([runs[v][n][c] for c in cases], labels) for n in args.runs}
        allres = [runs[v][n][c] for n in args.runs for c in cases]
        out[v] = {
            "pooled": pooled(allres, labels),
            "per_run": per_run,
            "repeatability": agreement(
                [
                    {c: key_decisions(runs[v][n][c], labels[c]) for c in cases}
                    for n in args.runs
                ]
            ),
        }
    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    main()
