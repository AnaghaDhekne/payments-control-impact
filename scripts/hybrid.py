"""Hybrid candidate recovery using observable metadata and narrative documents only."""
from __future__ import annotations
import json, re
from scripts.baseline import rank_controls

TOKEN=re.compile(r"[a-z0-9]+")
STOP={"the","a","an","and","or","of","to","in","for","is","are","with","from","this","that","change","control","payment"}

def tokens(text):
    return {x for x in TOKEN.findall((text or "").lower()) if x not in STOP and len(x)>2}

def retrieve_control_documents(case,top_k=20):
    q=tokens(case["change_ticket"]["title"]+" "+case["change_ticket"]["text"])
    rows=[]
    for d in case["control_documents"]:
        dt=tokens(d["title"]+" "+d["text"])
        score=len(q & dt)/(len(q | dt) or 1)
        rows.append({**d,"retrieval_score":score})
    rows.sort(key=lambda x:(-x["retrieval_score"],0 if x.get("criticality")=="KEY" else 1,x["control_id"]))
    return rows[:top_k]

def build_prompt(case,candidates,baseline_ids):
    docs="\\n".join("- %s | %s | %s | %s"%(d["control_id"],d["criticality"],d["title"],d["text"]) for d in candidates)
    return "Assess payment-control impact from observable evidence only. Return JSON only with key recommendations. Each item: control_id, decision (AFFECTED, UNAFFECTED, UNCERTAIN), actions, confidence, reason. Allowed actions: REASSESS_DESIGN, REFRESH_EVIDENCE, OUT_OF_CYCLE_TEST, CONTROL_GAP_REVIEW. Do not invent IDs. Prefer UNCERTAIN when ambiguous. Narrative evidence may recover missing metadata. Do not treat ticket control impact N/A as authoritative.\\nCHANGE TICKET\\n%s\\n%s\\nBASELINE IDS\\n%s\\nCANDIDATES\\n%s"%(case["change_ticket"]["title"],case["change_ticket"]["text"],sorted(baseline_ids),docs)

def parse_recommendations(raw,allowed):
    raw=(raw or "").strip()
    if not raw:
        raise ValueError("empty model response")
    if raw.startswith("```"): raw=re.sub(r"^```(?:json)?\\s*|\\s*```$","",raw,flags=re.I|re.S)
    try:
        obj=json.loads(raw)
    except json.JSONDecodeError:
        start=raw.find("{"); end=raw.rfind("}")
        if start < 0 or end <= start:
            raise ValueError("model response contained no JSON object")
        try:
            obj=json.loads(raw[start:end+1])
        except json.JSONDecodeError as exc:
            raise ValueError("model response JSON could not be decoded") from exc
    out=[]; seen=set()
    decisions={"AFFECTED","UNAFFECTED","UNCERTAIN"}
    valid_actions={"REASSESS_DESIGN","REFRESH_EVIDENCE","OUT_OF_CYCLE_TEST","CONTROL_GAP_REVIEW"}
    for x in obj.get("recommendations",[]):
        cid=x.get("control_id")
        if cid not in allowed or cid in seen or x.get("decision") not in decisions: continue
        out.append({"control_id":cid,"decision":x["decision"],"actions":[a for a in x.get("actions",[]) if a in valid_actions],"confidence":float(x.get("confidence",0.0)),"reason":str(x.get("reason",""))[:1000]})
        seen.add(cid)
    return out

def hybrid_rank_controls(case,llm,top_k=20):
    baseline=rank_controls(case); baseline_ids={x["control_id"] for x in baseline}
    retrieved=retrieve_control_documents(case,top_k)
    raw=llm(build_prompt(case,retrieved,baseline_ids))
    parse_error=None
    try:
        recs=parse_recommendations(raw,{d["control_id"] for d in retrieved})
    except ValueError as exc:
        recs=[]; parse_error=str(exc)
    recovered={x["control_id"] for x in recs if x["decision"] in {"AFFECTED","UNCERTAIN"}}
    return {"baseline":baseline,"retrieved":retrieved,"llm_recommendations":recs,"recommended_control_ids":sorted(baseline_ids|recovered),"uncertain_control_ids":sorted(x["control_id"] for x in recs if x["decision"]=="UNCERTAIN"),"parse_error":parse_error}
