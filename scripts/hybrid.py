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
    fenced=re.match(r"^\`\`\`(?:json)?\\s*([\\s\\S]*?)\\s*\`\`\`$",raw,flags=re.I)
    if fenced:
        raw=fenced.group(1).strip()
    try:
        obj=json.loads(raw)
    except json.JSONDecodeError as first_exc:
        starts=[(raw.find("{"),"}"),(raw.find("["),"]")]
        starts=[x for x in starts if x[0]>=0]
        if not starts:
            raise ValueError("model response contained no JSON object or array") from first_exc
        pos,closer=min(starts,key=lambda x:x[0])
        end=raw.rfind(closer)
        if end<=pos:
            raise ValueError("model response JSON could not be decoded") from first_exc
        try:
            obj=json.loads(raw[pos:end+1])
        except json.JSONDecodeError as exc:
            raise ValueError("model response JSON could not be decoded") from exc
    items=obj if isinstance(obj,list) else obj.get("recommendations",[])
    if not isinstance(items,list):
        raise ValueError("model response recommendations must be a list")
    out=[]; seen=set()
    decisions={"AFFECTED","UNAFFECTED","UNCERTAIN"}
    valid_actions={"REASSESS_DESIGN","REFRESH_EVIDENCE","OUT_OF_CYCLE_TEST","CONTROL_GAP_REVIEW"}
    confidence_map={"LOW":0.33,"MEDIUM":0.67,"HIGH":1.0}
    for x in items:
        cid=x.get("control_id")
        if cid not in allowed or cid in seen or x.get("decision") not in decisions: continue
        raw_conf=x.get("confidence",0.0)
        try:
            confidence=float(raw_conf)
        except (TypeError,ValueError):
            confidence=confidence_map.get(str(raw_conf).upper(),0.0)
        out.append({"control_id":cid,"decision":x["decision"],"actions":[a for a in x.get("actions",[]) if a in valid_actions],"confidence":confidence,"reason":str(x.get("reason",""))[:1000]})
        seen.add(cid)
    return out

def hybrid_rank_controls(case, llm, top_k=20, **kwargs):
    """
    Merge baseline and LLM recommendations for a single change scenario.

    Args:
        case: dict representing synthetic change scenario
        llm: callable that takes a case dict and returns a raw JSON string
        top_k: int, number of candidate control documents to retrieve and pass to the LLM

    Returns:
        Dict with keys:
            baseline: list of baseline-ranked control dicts (each has control_id)
            recommended_control_ids: sorted list of control IDs (baseline union LLM)
            parse_error: error message string if LLM response could not be parsed, else None
            raw_model_response: the raw string returned by llm(case)
    """
    candidates = retrieve_control_documents(case, top_k)
    allowed = {d["control_id"] for d in candidates}
    baseline = rank_controls(case)
    baseline_ids = {x["control_id"] for x in baseline}

    prompt = build_prompt(case, candidates, baseline_ids)
    raw = llm(prompt) if callable(llm) else str(llm)

    parse_error = None
    try:
        recommendations = parse_recommendations(raw, allowed)
    except (ValueError, json.JSONDecodeError) as exc:
        recommendations = []
        parse_error = str(exc)

    recommended_ids = set(baseline_ids)
    for r in recommendations:
        recommended_ids.add(r["control_id"])

    return {
        "baseline": baseline,
        "recommended_control_ids": sorted(recommended_ids),
        "parse_error": parse_error,
        "raw_model_response": raw,
    }

