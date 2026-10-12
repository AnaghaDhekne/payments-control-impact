"""Compare old Jaccard-only retrieval vs new field-aware retrieval.

Measures candidate-set recall of truly affected key controls and false
candidate count at top_k=20 and top_k=30 on the development split.
Ground truth is loaded only here, never in hybrid.py.
"""

from __future__ import annotations
import json
from scripts.hybrid import retrieve_control_documents, tokens
from scripts.evaluate_baseline import _truth_by_change
from scripts.generate_benchmark import build_graph, build_changes
from scripts.generate_observable import build_condition


def retrieve_jaccard_only(case, top_k=20):
    """Old retrieval: pure token Jaccard, no field-aware bonus."""
    q = tokens(case["change_ticket"]["title"] + " " + case["change_ticket"]["text"])
    rows = []
    for d in case["control_documents"]:
        dt = tokens(d["title"] + " " + d["text"])
        jaccard = len(q & dt) / (len(q | dt) or 1)
        rows.append({**d, "jaccard_score": jaccard})
    rows.sort(
        key=lambda x: (
            -x["jaccard_score"],
            0 if x.get("criticality") == "KEY" else 1,
            x["control_id"],
        )
    )
    return rows[:top_k]


def evaluate_retrieval(retrieve_fn, case, truth, top_k):
    """Measure candidate-set recall for one case under one retrieval method."""
    candidates = retrieve_fn(case, top_k=top_k)
    candidate_ids = {c["control_id"] for c in candidates}
    labels = truth[case["change_id"]]
    affected = {cid for cid, x in labels.items() if x.affected}
    key = {cid for cid, x in labels.items() if x.affected and x.criticality == "KEY"}
    key_in_candidates = key & candidate_ids
    affected_in_candidates = affected & candidate_ids
    false_candidates = candidate_ids - affected
    return {
        "change_id": case["change_id"],
        "top_k": top_k,
        "candidate_count": len(candidate_ids),
        "key_control_pairs": len(key),
        "key_in_candidates": len(key_in_candidates),
        "key_recall": 1.0 if not key else len(key_in_candidates) / len(key),
        "affected_pairs": len(affected),
        "affected_in_candidates": len(affected_in_candidates),
        "affected_recall": (
            1.0 if not affected else len(affected_in_candidates) / len(affected)
        ),
        "false_candidates": len(false_candidates),
        "missed_key_ids": sorted(key - candidate_ids),
    }


def retrieve_graph_aware(case, top_k=20):
    """Graph-aware retrieval: lexical + graph-neighbor expansion.

    Starts with field-aware lexical retrieval, then expands to include
    controls within 2 hops of changed entities in the visible graph.
    This catches controls connected structurally (e.g. C06 'Outbound
    message transformation' for a 'Creditor country code' change) that
    have zero lexical overlap with the ticket text.
    """
    # Step 1: lexical retrieval (field-aware)
    lexical = retrieve_control_documents(case, top_k=top_k)
    candidate_ids = {r["control_id"] for r in lexical}

    # Step 2: graph-neighbor expansion (2-hop)
    vnodes = {n["id"]: n for n in case.get("visible_metadata", {}).get("nodes", [])}
    vis_edges = case.get("visible_metadata", {}).get("edges", [])
    changed_ids = set(case["change_ticket"].get("changed_entity_ids", []))

    # 1-hop neighbors
    hop1 = set(changed_ids)
    for e in vis_edges:
        if e["source"] in changed_ids or e["target"] in changed_ids:
            hop1.add(e["source"])
            hop1.add(e["target"])

    # 2-hop neighbors
    hop2 = set(hop1)
    for e in vis_edges:
        if e["source"] in hop1 or e["target"] in hop1:
            hop2.add(e["source"])
            hop2.add(e["target"])

    # Controls reachable within 2 hops that are NOT already in lexical results
    graph_controls = {
        nid for nid in hop2
        if vnodes.get(nid, {}).get("type") == "CONTROL" and nid not in candidate_ids
    }

    # Add graph-neighbor controls with a small score boost
    docs_by_id = {d["control_id"]: d for d in case["control_documents"]}
    rows = list(lexical)
    for cid in sorted(graph_controls):
        if cid in docs_by_id:
            d = docs_by_id[cid]
            rows.append({
                **d,
                "retrieval_score": 0.0,  # graph neighbor, no lexical score
                "jaccard_score": 0.0,
                "name_overlap": 0.0,
                "graph_neighbor": True,
            })

    # Sort: lexical results first (by retrieval_score), then graph neighbors (by criticality)
    rows.sort(
        key=lambda x: (
            -x.get("retrieval_score", 0.0),
            0 if x.get("criticality") == "KEY" else 1,
            x["control_id"],
        )
    )
    return rows[:top_k]


def compare(level=30, mode="correlated", split="development"):
    """Run the full comparison and return aggregate results."""
    graph = build_graph()
    changes = build_changes()
    truth = _truth_by_change(graph, changes)
    obs = build_condition(graph, changes, level, mode)
    cases = [c for c in obs["cases"] if c["split"] == split]

    methods = {
        "jaccard_only": retrieve_jaccard_only,
        "field_aware": retrieve_control_documents,
        "graph_aware": retrieve_graph_aware,
    }
    top_ks = [20, 30, 50]
    results = {}

    for method_name, fn in methods.items():
        for tk in top_ks:
            per_case = []
            total_key = 0
            key_found = 0
            total_aff = 0
            aff_found = 0
            total_false = 0
            all_missed = []
            for case in cases:
                r = evaluate_retrieval(fn, case, truth, tk)
                per_case.append(r)
                total_key += r["key_control_pairs"]
                key_found += r["key_in_candidates"]
                total_aff += r["affected_pairs"]
                aff_found += r["affected_in_candidates"]
                total_false += r["false_candidates"]
                all_missed.extend(r["missed_key_ids"])
            results[f"{method_name}_k{tk}"] = {
                "method": method_name,
                "top_k": tk,
                "cases": len(cases),
                "total_key_pairs": total_key,
                "key_in_candidates": key_found,
                "key_candidate_recall": 1.0 if not total_key else key_found / total_key,
                "total_affected_pairs": total_aff,
                "affected_in_candidates": aff_found,
                "affected_candidate_recall": (
                    1.0 if not total_aff else aff_found / total_aff
                ),
                "total_false_candidates": total_false,
                "avg_false_per_case": total_false / len(cases) if cases else 0,
                "missed_key_ids": all_missed,
                "per_case": per_case,
            }

    return results


if __name__ == "__main__":
    r = compare()
    # Print summary table
    print(
        f"{'Method':<20} {'k':>3} {'Key Pairs':>10} {'Key Found':>10} {'Key Recall':>10} {'Aff Recall':>10} {'False/Case':>10}"
    )
    print("-" * 80)
    for key, v in r.items():
        print(
            f"{v['method']:<20} {v['top_k']:>3} {v['total_key_pairs']:>10} {v['key_in_candidates']:>10} "
            f"{v['key_candidate_recall']:>10.1%} {v['affected_candidate_recall']:>10.1%} {v['avg_false_per_case']:>10.1f}"
        )
    print()
    # Show missed key IDs for each method
    for key, v in r.items():
        missed = v["missed_key_ids"]
        print(
            f"{v['method']} k={v['top_k']}: missed {len(missed)} key controls: {missed}"
        )
    print()
    print(json.dumps(r, indent=2))
