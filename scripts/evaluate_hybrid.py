"""Evaluate the hybrid on the frozen benchmark. Ground truth is loaded only here."""
from __future__ import annotations
import argparse, json
from scripts.hybrid import hybrid_rank_controls
from scripts.evaluate_baseline import _truth_by_change
from scripts.generate_benchmark import build_graph, build_changes
from scripts.generate_observable import build_condition

def evaluate_hybrid(llm, level=30, mode="correlated", split="development", runs=1, top_k=20, max_cases=None, progress=False):
    graph=build_graph(); changes=build_changes(); truth=_truth_by_change(graph,changes)
    obs=build_condition(graph,changes,level,mode)
    selected=[c for c in obs["cases"] if c["split"]==split]
    if max_cases is not None:
        selected=selected[:max_cases]
    run_results=[]
    for run in range(runs):
        total_key=base_key=final_key=total_aff=final_aff=base_work=final_work=0
        decisions={}; parse_failures=[]
        for idx,case in enumerate(selected,1):
            if progress:
                print(f"[run {run+1}/{runs}] case {idx}/{len(selected)}: {case['change_id']}",flush=True)
            out=hybrid_rank_controls(case,llm,top_k)
            base={x["control_id"] for x in out["baseline"]}; final=set(out["recommended_control_ids"])
            if out.get("parse_error"):
                parse_failures.append({"change_id":case["change_id"],"error":out["parse_error"],"raw_model_response":out.get("raw_model_response")})
            labels=truth[case["change_id"]]
            aff={cid for cid,x in labels.items() if x.affected}
            key={cid for cid,x in labels.items() if x.affected and x.criticality=="KEY"}
            total_key+=len(key); base_key+=len(key&base); final_key+=len(key&final)
            total_aff+=len(aff); final_aff+=len(aff&final); base_work+=len(base); final_work+=len(final)
            decisions[case["change_id"]]=sorted(final)
        misses=total_key-base_key; recovered=final_key-base_key
        run_results.append({"run":run+1,"key_control_pairs":total_key,"baseline_key_hits":base_key,"final_key_hits":final_key,
          "baseline_key_misses":misses,"recovered_key_misses":recovered,"key_miss_recovery_rate":0 if not misses else recovered/misses,
          "final_key_recall":1 if not total_key else final_key/total_key,"final_affected_recall":1 if not total_aff else final_aff/total_aff,
          "baseline_workload":base_work,"final_workload":final_work,"workload_increase_rate":0 if not base_work else (final_work-base_work)/base_work,
          "parse_failure_count":len(parse_failures),"parse_failures":parse_failures,"decisions":decisions})
    agreement=1.0
    if runs>1:
        pairs=[]
        key_ids=[n["id"] for n in graph["nodes"] if n["type"]=="CONTROL" and n.get("criticality")=="KEY"]
        for case in selected:
            for cid in key_ids:
                vals=[cid in r["decisions"][case["change_id"]] for r in run_results]
                pairs.append(1.0 if all(v==vals[0] for v in vals) else 0.0)
        agreement=sum(pairs)/len(pairs) if pairs else 1.0
    return {"level":level,"mode":mode,"split":split,"cases":len(selected),"runs":runs,"top_k":top_k,
            "key_prediction_exact_agreement":agreement,"repeated_run_agreement":agreement,"runs_detail":run_results}

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--model",default="databricks-llama-4-maverick")
    p.add_argument("--runs",type=int,default=1); p.add_argument("--top-k",type=int,default=20)
    p.add_argument("--split",choices=["development","test"],default="development")
    p.add_argument("--level",type=int,choices=[0,30,60],default=30)
    p.add_argument("--mode",choices=["random","correlated"],default="correlated")
    p.add_argument("--max-cases",type=int)
    a=p.parse_args()
    from scripts.databricks_llm import DatabricksChatLLM
    result=evaluate_hybrid(DatabricksChatLLM(a.model),level=a.level,mode=a.mode,split=a.split,runs=a.runs,top_k=a.top_k,max_cases=a.max_cases,progress=True)
    print(json.dumps(result,indent=2))
