"""Combine repeat runs of the same cases by majority vote, and measure stability.

    python -m scripts.ensemble /Volumes/workspace/default/detective_runs/fresh-C \
        --groups 1,2,3 4,5,6

Each group of runs (run<N>/<case>.json) becomes one ensemble answer per case:

* a control is recommended when the rules baseline reaches it, or when a
  majority of the group's runs recommend it (final decision AFFECTED);
* otherwise it is a review item when a majority of runs either recommend it
  or send it to review (AFFECTED or UNCERTAIN);
* otherwise it is not flagged.

Review items are ranked: more runs agreeing first, then key controls.

Stability is reported two ways, both on affected key controls only:
* ensemble agreement: share of (case, key control) pairs given the same
  recommend / not-recommend decision by every group (the pre-registered
  measure for majority voting);
* single-run agreement: the same, between every pair of individual runs, for
  comparison with a single-run agent.

Labels are computed offline here and never reach a model. Writes
ensemble.json in the folder and prints the summary.
"""

from __future__ import annotations

import argparse
import itertools
import json
from pathlib import Path

from scripts.evaluate_baseline import _truth_by_change
from scripts.generate_benchmark import build_changes, build_graph
from scripts.run_detective_suite import aggregate, labels_for
from scripts.score_detective import score


def load_run(folder: Path, run: int) -> dict[str, dict]:
    out = {}
    for p in sorted((folder / f"run{run}").glob("CHG-*.json")):
        if ".calls" in p.name:
            continue
        r = json.loads(p.read_text())
        if "coverage" in r:  # finished cases only
            out[r["change_id"]] = r
    return out


def combine(results: list[dict]) -> dict:
    """Majority vote over runs of one case; returns a result scored like a run."""
    need = len(results) // 2 + 1
    baseline = results[0]["baseline"]
    base_ids = {b["control_id"] for b in baseline}
    rec_votes, flag_votes, decided = {}, {}, {}
    for r in results:
        rec = set(r["recommended_control_ids"]) - base_ids
        unc = set(r["uncertain_control_ids"])
        for c in rec:
            rec_votes[c] = rec_votes.get(c, 0) + 1
        for c in rec | unc:
            flag_votes[c] = flag_votes.get(c, 0) + 1
        for f in r.get("findings", []):
            decided[f["control_id"]] = decided.get(f["control_id"], 0) + 1
    recommended = base_ids | {c for c, v in rec_votes.items() if v >= need}
    review = {c for c, v in flag_votes.items() if v >= need and c not in recommended}
    all_controls = set(results[0]["uninvestigated_control_ids"]) | set(decided)
    undecided = {c for c in all_controls if decided.get(c, 0) < need}
    queue = sorted(
        review,
        key=lambda c: (-flag_votes[c], -rec_votes.get(c, 0), c),
    )
    return {
        "change_id": results[0]["change_id"],
        "baseline": baseline,
        "recommended_control_ids": sorted(recommended),
        "uncertain_control_ids": sorted(review),
        "uninvestigated_control_ids": sorted(undecided - recommended - review),
        "ranked_review_queue": [
            {"control_id": c, "runs_flagging": flag_votes[c]} for c in queue
        ],
        # model calls, summed over the runs (cost of the ensemble)
        "trace": [e for r in results for e in r["trace"]],
        "status": "ENSEMBLE",
    }


def key_decisions(result: dict, labels: dict) -> dict[str, str]:
    rec = set(result["recommended_control_ids"])
    return {k: ("REC" if k in rec else "NOT") for k in labels["key_control_ids"]}


def agreement(decision_sets: list[dict[str, dict[str, str]]]) -> dict:
    """Share of (case, key control) pairs with the same decision in every set."""
    pairs = agree = 0
    for cid in decision_sets[0]:
        for ctrl in decision_sets[0][cid]:
            vals = {d.get(cid, {}).get(ctrl) for d in decision_sets}
            pairs += 1
            agree += len(vals) == 1
    return {"key_pairs": pairs, "agreement": agree / pairs if pairs else None}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("folder")
    parser.add_argument(
        "--groups",
        nargs="+",
        required=True,
        help="Run numbers per ensemble, e.g. 1,2,3 4,5,6",
    )
    args = parser.parse_args()
    folder = Path(args.folder)
    groups = [[int(x) for x in g.split(",")] for g in args.groups]
    runs = {n: load_run(folder, n) for g in groups for n in g}
    cases = sorted(set.intersection(*(set(r) for r in runs.values())))
    missing = {n: sorted(set().union(*runs.values()) - set(r)) for n, r in runs.items()}
    truth = _truth_by_change(build_graph(), build_changes())
    labels = {cid: labels_for(truth[cid]) for cid in cases}

    out = {"folder": str(folder), "groups": groups, "cases": cases, "ensembles": []}
    ensemble_decisions = []
    for g in groups:
        metrics, decisions, queues = [], {}, {}
        for cid in cases:
            res = combine([runs[n][cid] for n in g])
            m = score(res, labels[cid])
            m.update(
                change_id=cid,
                status="ENSEMBLE",
                baseline_controls=len(res["baseline"]),
            )
            metrics.append(m)
            decisions[cid] = key_decisions(res, labels[cid])
            affected = set(labels[cid]["affected_control_ids"])
            queues[cid] = [
                {**q, "affected": q["control_id"] in affected}
                for q in res["ranked_review_queue"]
            ]
        ensemble_decisions.append(decisions)
        # Ranked queue quality: affected share in the top half vs the bottom half.
        top = bottom = top_true = bottom_true = 0
        for q in queues.values():
            half = (len(q) + 1) // 2
            top += half
            bottom += len(q) - half
            top_true += sum(i["affected"] for i in q[:half])
            bottom_true += sum(i["affected"] for i in q[half:])
        out["ensembles"].append(
            {
                "runs": g,
                "summary": aggregate(metrics, "test", "ensemble"),
                "cases": metrics,
                "ranked_queue": {
                    "top_half_true_share": top_true / top if top else None,
                    "bottom_half_true_share": (
                        bottom_true / bottom if bottom else None
                    ),
                },
            }
        )
    single = [
        {cid: key_decisions(runs[n][cid], labels[cid]) for cid in cases}
        for g in groups
        for n in g
    ]
    pairwise = [agreement([a, b]) for a, b in itertools.combinations(single, 2)]
    out["stability"] = {
        "ensemble_agreement": (
            agreement(ensemble_decisions) if len(groups) > 1 else None
        ),
        "single_run_pairwise_agreement_mean": (
            sum(p["agreement"] for p in pairwise) / len(pairwise) if pairwise else None
        ),
        "single_run_all_agree": agreement(single),
        "target": 0.95,
    }
    out["incomplete_cases_by_run"] = {n: m for n, m in missing.items() if m}
    (folder / "ensemble.json").write_text(json.dumps(out, indent=2) + "\n")
    for e in out["ensembles"]:
        print(f"runs {e['runs']}:", json.dumps(e["summary"], indent=2))
        print("  ranked queue:", e["ranked_queue"])
    print("stability:", json.dumps(out["stability"], indent=2))
    if out["incomplete_cases_by_run"]:
        print("cases missing from some runs:", out["incomplete_cases_by_run"])


if __name__ == "__main__":
    main()
