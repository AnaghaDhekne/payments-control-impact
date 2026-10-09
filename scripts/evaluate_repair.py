"""Lineage repair comparator (Experiment F).

Simulates repairing observable metadata edges and measures baseline key-control
recall vs workload. Compares against AI-assisted recovery to determine
whether fixing metadata is more effective than adding LLM analysis.

No LLM calls required — pure baseline measurement.
"""
from __future__ import annotations
import argparse, json, random, hashlib
from scripts.baseline import rank_controls
from scripts.evaluate_baseline import _truth_by_change
from scripts.generate_benchmark import build_graph, build_changes
from scripts.generate_observable import build_condition, stable_seed

def evaluate_repair(level=30, mode="correlated", split="development", repair_fractions=(0.0, 0.1, 0.2, 0.3, 0.5, 1.0)):
    graph=build_graph(); changes=build_changes(); truth=_truth_by_change(graph,changes)
    obs=build_condition(graph,changes,level,mode)
    selected=[c for c in obs["cases"] if c["split"]==split]
    all_edges={e["id"]:e for e in graph["edges"] if e.get("metadata_exposable",True)}
    results=[]
    for frac in repair_fractions:
        total_key=base_key=base_work=0
        for case in selected:
            repaired_edges=[e.copy() for e in case["visible_metadata"]["edges"]]
            if frac>0:
                removed=case["degradation_manifest"]["removed_edge_ids"]
                rng=random.Random(stable_seed(20261007,case["change_id"],level,mode,"repair"))
                n_repair=round(len(removed)*frac)
                to_restore=rng.sample(removed,min(n_repair,len(removed)))
                for eid in to_restore:
                    if eid in all_edges:
                        repaired_edges.append(all_edges[eid].copy())
            repaired_case=dict(case)
            repaired_case["visible_metadata"]={"nodes":case["visible_metadata"]["nodes"],"edges":repaired_edges}
            baseline=rank_controls(repaired_case)
            base={x["control_id"] for x in baseline}
            labels=truth[case["change_id"]]
            key={cid for cid,x in labels.items() if x.affected and x.criticality=="KEY"}
            total_key+=len(key); base_key+=len(key&base); base_work+=len(base)
        misses=total_key-base_key
        results.append({
            "repair_fraction":frac,
            "key_control_pairs":total_key,
            "baseline_key_hits":base_key,
            "baseline_key_misses":misses,
            "baseline_key_recall":1 if not total_key else base_key/total_key,
            "baseline_workload":base_work,
        })
    return {"level":level,"mode":mode,"split":split,"cases":len(selected),"repair_results":results}

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--level",type=int,choices=[0,30,60],default=30)
    p.add_argument("--mode",choices=["random","correlated"],default="correlated")
    p.add_argument("--split",choices=["development","test"],default="development")
    a=p.parse_args()
    result=evaluate_repair(level=a.level,mode=a.mode,split=a.split)
    print(json.dumps(result,indent=2))
