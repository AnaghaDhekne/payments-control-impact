"""Evaluate the hybrid on the frozen benchmark. Ground truth is loaded only here."""
from __future__ import annotations
import argparse,json
from scripts.hybrid import hybrid_rank_controls
from scripts.evaluate_baseline import _truth_by_change
from scripts.generate_benchmark import build_graph,build_changes
from scripts.generate_observable import build_condition

def evaluate_hybrid(llm,level=30,mode="correlated",split="test",runs=1,top_k=20):
    graph=build_graph(); changes=build_changes(); truth=_truth_by_change(graph,changes)
    obs=build_condition(graph,changes,level,mode)
    selected=[c for c in obs["cases"] if c["split"]==split]
    run_results=[]
    for run in range(runs):
        total_key=base_key=final_key=total_aff=final_aff=base_work=final_work=0; decisions={}
        for case in selected:
            out=hybrid_rank_controls(case,llm,top_k)
            base={x["control_id"] for x in out["baseline"]}; final=set(out["recommended_control_ids"])
            labels=truth[case["change_id"]]
            aff={cid for cid,x in labels.items() if x.affected}; key={cid for cid,x in labels.items() if x.affected and x.criticality=="KEY"}
            total_key+=len(key); base_key+=len(key&base); final_key+=len(key&final)
            total_aff+=len(aff); final_aff+=len(aff&final); base_work+=len(base); final_work+=len(final)
            decisions[case["change_id"]]=sorted(final)
        misses=total_key-base_key; recovered=final_key-base_key
        run_results.append({"run":run+1,"key_control_pairs":total_key,"baseline_key_hits":base_key,"final_key_hits":final_key,
          "baseline_key_misses":misses,"recovered_key_misses":recovered,"key_miss_recovery_rate":0 if not misses else recovered/misses,
          "final_key_recall":1 if not total_key else final_key/total_key,"final_affected_recall":1 if not total_aff else final_aff/total_aff,
          "baseline_workload":base_work,"final_workload":final_work,"workload_increase_rate":0 if not base_work else (final_work-base_work)/base_work,
          "decisions":decisions})
    agreement=1.0
    if runs>1:
        pairs=[]
        control_ids=[n["id"] for n in graph["nodes"] if n["type"]=="CONTROL"]
        for case in selected:
            for cid in control_ids:
                vals=[cid in r["decisions"][case["change_id"]] for r in run_results]
                pairs.append(max(sum(vals),runs-sum(vals))/runs)
        agreement=sum(pairs)/len(pairs)
    summary={"level":level,"mode":mode,"runs":runs,"top_k":top_k,"repeated_run_agreement":agreement,"runs_detail":run_results}
    return summary

if __name__=="__main__":
    p=argparse.ArgumentParser(); p.add_argument("--model",default="system.ai.llama-4-maverick"); p.add_argument("--runs",type=int,default=1); p.add_argument("--top-k",type=int,default=20)
    a=p.parse_args()
    from scripts.databricks_llm import DatabricksChatLLM
    print(json.dumps(evaluate_hybrid(DatabricksChatLLM(a.model),runs=a.runs,top_k=a.top_k),indent=2))
