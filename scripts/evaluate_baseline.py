"""Evaluate metadata-only baseline against hidden labels.

Ground truth is loaded only here, never in baseline.py.
"""
from __future__ import annotations
import json
from pathlib import Path
from scripts.baseline import rank_controls
from scripts.ground_truth import Change,label_change
from scripts.generate_benchmark import build_graph,build_changes
from scripts.generate_observable import build_condition

def _truth_by_change(graph,changes):
    out={}
    for c in changes:
        ch=Change(c["change_id"],tuple(c["changed_node_ids"]),c["change_type"],c["implementation_date"],c["material"],c.get("rollback_date"))
        labels=label_change(graph,ch,test_period_start="2026-10-01",test_period_end="2027-03-31")
        out[c["change_id"]]={x.control_id:x for x in labels}
    return out

def evaluate_condition(level:int,mode:str,split:str="test")->dict:
    graph=build_graph(); changes=build_changes(); truth=_truth_by_change(graph,changes)
    observable=build_condition(graph,changes,level,mode)
    cases=[]; total_key=0; found_key=0; total_affected=0; found_affected=0; workload=0
    unreachable_key=0
    for case in observable["cases"]:
        if case["split"]!=split: continue
        ranked=rank_controls(case)
        recommended={x["control_id"] for x in ranked}
        labels=truth[case["change_id"]]
        affected={cid for cid,x in labels.items() if x.affected}
        key={cid for cid,x in labels.items() if x.affected and x.criticality=="KEY"}
        got=affected & recommended; got_key=key & recommended
        total_affected+=len(affected); found_affected+=len(got)
        total_key+=len(key); found_key+=len(got_key)
        workload+=len(recommended)
        unreachable_key+=len(key-recommended)
        cases.append({
          "change_id":case["change_id"],
          "affected_controls":len(affected),"reachable_affected":len(got),
          "affected_key_controls":len(key),"reachable_key_controls":len(got_key),
          "recommended_controls":len(recommended),
          "key_control_recall":1.0 if not key else len(got_key)/len(key)
        })
    return {
      "level":level,"mode":mode,"split":split,"cases":len(cases),
      "affected_pairs":total_affected,"key_control_pairs":total_key,
      "reachable_affected_pairs":found_affected,"reachable_key_control_pairs":found_key,
      "affected_recall":1.0 if not total_affected else found_affected/total_affected,
      "key_control_recall":1.0 if not total_key else found_key/total_key,
      "reviewer_workload":workload,
      "unreachable_key_control_pairs":unreachable_key,
      "case_results":cases
    }

def evaluate_matrix():
    return [evaluate_condition(l,m) for l in (0,30,60) for m in ("random","correlated")]

if __name__=="__main__":
    print(json.dumps(evaluate_matrix(),indent=2))
