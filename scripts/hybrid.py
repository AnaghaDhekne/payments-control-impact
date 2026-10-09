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
    # Field-aware: extract changed entity names and types from visible metadata
    changed_ids=set(case["change_ticket"].get("changed_entity_ids",[]))
    vnodes={n["id"]:n for n in case.get("visible_metadata",{}).get("nodes",[])}
    changed_name_tokens=set()
    for nid in changed_ids:
        n=vnodes.get(nid)
        if n:
            changed_name_tokens|=tokens(n.get("name",""))
            changed_name_tokens|=tokens(n.get("description",""))
    rows=[]
    for d in case["control_documents"]:
        dt=tokens(d["title"]+" "+d["text"])
        jaccard=len(q & dt)/(len(q | dt) or 1)
        # Field-aware bonus: changed entity name tokens in control text
        name_overlap=len(changed_name_tokens & dt)/(len(changed_name_tokens) or 1) if changed_name_tokens else 0
        score=jaccard+0.5*name_overlap
        rows.append({**d,"retrieval_score":score,"jaccard_score":jaccard,"name_overlap":name_overlap})
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

def hybrid_rank_controls(case, llm, top_k=20, min_confidence=0.0, cap=None, uncertain_cap=None, **kwargs):
    """
    Merge baseline and LLM recommendations for a single change scenario.

    Args:
        case: dict representing synthetic change scenario
        llm: callable that takes a prompt string and returns a raw JSON string
        top_k: int, number of candidate control documents to retrieve and pass to the LLM
        min_confidence: float, minimum confidence for LLM-only AFFECTED (default 0.0 = keep all)
        cap: int or None, max number of LLM-only AFFECTED additions (default None = no cap)
        uncertain_cap: int or None, max number of LLM-only UNCERTAIN items surfaced for review (default None = no cap)

    Returns:
        Dict with keys:
            baseline: list of baseline-ranked control dicts (each has control_id)
            recommended_control_ids: sorted list (baseline + LLM AFFECTED only)
            uncertain_control_ids: sorted list (LLM UNCERTAIN, surfaced for review)
            unaffected_control_ids: sorted list (LLM UNAFFECTED, not surfaced)
            llm_recommendations: raw parsed LLM recommendation dicts
            parse_error: error message string if LLM response could not be parsed, else None
            raw_model_response: the raw string returned by llm(prompt)
            audit_rows: per-control audit records for evaluation
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

    # Separate LLM recommendations by decision, filtering by confidence
    llm_affected = set()
    llm_uncertain = set()
    llm_unaffected = set()
    rec_by_id = {r["control_id"]: r for r in recommendations}
    # LLM-only AFFECTED candidates ranked by confidence (for capping)
    llm_only_affected = []
    # LLM-only UNCERTAIN candidates ranked by confidence (for capping)
    llm_only_uncertain = []

    for r in recommendations:
        decision = r.get("decision", "").upper()
        cid = r["control_id"]
        conf = r.get("confidence", 0.0)
        if decision == "AFFECTED":
            if cid not in baseline_ids:
                llm_only_affected.append((cid, conf))
            if conf >= min_confidence:
                llm_affected.add(cid)
        elif decision == "UNCERTAIN":
            if cid not in baseline_ids:
                llm_only_uncertain.append((cid, conf))
            llm_uncertain.add(cid)
        elif decision == "UNAFFECTED":
            llm_unaffected.add(cid)

    # Apply cap: keep only top N LLM-only AFFECTED by confidence
    if cap is not None and llm_only_affected:
        llm_only_affected.sort(key=lambda x: (-x[1], x[0]))
        capped_ids = {cid for cid, _ in llm_only_affected[:cap]}
        llm_affected = {cid for cid in llm_affected if cid in baseline_ids or cid in capped_ids}

    # Apply uncertain_cap: keep only top N LLM-only UNCERTAIN by confidence
    if uncertain_cap is not None and llm_only_uncertain:
        llm_only_uncertain.sort(key=lambda x: (-x[1], x[0]))
        capped_uncertain_ids = {cid for cid, _ in llm_only_uncertain[:uncertain_cap]}
        # Demote non-capped uncertain to unaffected (not surfaced for review)
        demoted = {cid for cid in llm_uncertain if cid not in baseline_ids and cid not in capped_uncertain_ids}
        llm_uncertain = {cid for cid in llm_uncertain if cid in baseline_ids or cid in capped_uncertain_ids}
        llm_unaffected |= demoted

    # Positive recommendations: baseline + LLM AFFECTED only
    recommended_ids = set(baseline_ids) | llm_affected

    # UNCERTAIN controls surfaced for review but not positive recommendations
    uncertain_ids = sorted(llm_uncertain - baseline_ids)

    # UNAFFECTED controls not surfaced but tracked for audit
    unaffected_ids = sorted(llm_unaffected)

    # Build per-control audit rows with changed entity context
    changed_ids = set(case["change_ticket"].get("changed_entity_ids", []))
    vnodes = {n["id"]: n for n in case.get("visible_metadata", {}).get("nodes", [])}
    changed_names = [vnodes.get(nid, {}).get("name", "") for nid in changed_ids if nid in vnodes]
    changed_types = [vnodes.get(nid, {}).get("type", "") for nid in changed_ids if nid in vnodes]
    audit_rows = []
    all_ids = recommended_ids | set(uncertain_ids) | set(unaffected_ids)
    for cid in sorted(all_ids):
        rec = rec_by_id.get(cid, {})
        audit_rows.append({
            "control_id": cid,
            "baseline_flag": cid in baseline_ids,
            "raw_decision": rec.get("decision"),
            "confidence": rec.get("confidence"),
            "actions": rec.get("actions", []),
            "reason": rec.get("reason", ""),
            "changed_entity_ids": sorted(changed_ids),
            "changed_entity_names": changed_names,
            "changed_entity_types": changed_types,
            "final_class": "AFFECTED" if cid in recommended_ids else ("UNCERTAIN" if cid in uncertain_ids else "UNAFFECTED"),
            "surfaced_for_review": cid in recommended_ids or cid in llm_uncertain,
        })

    return {
        "baseline": baseline,
        "recommended_control_ids": sorted(recommended_ids),
        "uncertain_control_ids": uncertain_ids,
        "unaffected_control_ids": unaffected_ids,
        "llm_recommendations": recommendations,
        "parse_error": parse_error,
        "raw_model_response": raw,
        "audit_rows": audit_rows,
    }


def build_verification_prompt(case, to_verify, candidates, baseline_ids):
    """Stage 2 prompt: verify each candidate with cited evidence from both sources."""
    cand_by_id = {c["control_id"]: c for c in candidates}
    docs = "\n".join("- %s | %s | %s | %s" % (
        v["control_id"],
        cand_by_id.get(v["control_id"], {}).get("criticality", ""),
        cand_by_id.get(v["control_id"], {}).get("title", ""),
        cand_by_id.get(v["control_id"], {}).get("text", "")
    ) for v in to_verify)
    return (
        "Verify whether each control is truly impacted by this change. "
        "For each control, you MUST cite:\n"
        "1. A specific phrase from the CHANGE TICKET suggesting impact on this control\n"
        "2. A specific phrase from the CONTROL DOCUMENT indicating susceptibility\n"
        "If you cannot cite specific evidence from BOTH sources, classify as UNAFFECTED. "
        "Only AFFECTED if evidence from both is clear and specific. "
        "UNCERTAIN only if evidence is partial or ambiguous.\n"
        "Return JSON only. Each item: control_id, decision (AFFECTED, UNAFFECTED, UNCERTAIN), "
        "evidence_ticket (exact quote from ticket or empty), evidence_control (exact quote from control doc or empty), "
        "confidence (0-1), reason.\n"
        "CHANGE TICKET\n%s\n%s\n"
        "CONTROLS TO VERIFY\n%s"
    ) % (case["change_ticket"]["title"], case["change_ticket"]["text"], docs)


def parse_verification_response(raw, allowed):
    """Parse stage 2 verification response with evidence fields."""
    raw = (raw or "").strip()
    if not raw:
        raise ValueError("empty model response")
    fenced = re.match(r"^```(?:json)?\s*([\s\S]*?)\s*```$", raw, flags=re.I)
    if fenced:
        raw = fenced.group(1).strip()
    try:
        obj = json.loads(raw)
    except json.JSONDecodeError as first_exc:
        starts = [(raw.find("{"), "}"), (raw.find("["), "]")]
        starts = [x for x in starts if x[0] >= 0]
        if not starts:
            raise ValueError("model response contained no JSON object or array") from first_exc
        pos, closer = min(starts, key=lambda x: x[0])
        end = raw.rfind(closer)
        if end <= pos:
            raise ValueError("model response JSON could not be decoded") from first_exc
        try:
            obj = json.loads(raw[pos:end + 1])
        except json.JSONDecodeError as exc:
            raise ValueError("model response JSON could not be decoded") from exc
    items = obj if isinstance(obj, list) else obj.get("recommendations", [])
    if not isinstance(items, list):
        raise ValueError("model response recommendations must be a list")
    out = []
    seen = set()
    decisions = {"AFFECTED", "UNAFFECTED", "UNCERTAIN"}
    confidence_map = {"LOW": 0.33, "MEDIUM": 0.67, "HIGH": 1.0}
    for x in items:
        cid = x.get("control_id")
        if cid not in allowed or cid in seen or x.get("decision") not in decisions:
            continue
        raw_conf = x.get("confidence", 0.0)
        try:
            confidence = float(raw_conf)
        except (TypeError, ValueError):
            confidence = confidence_map.get(str(raw_conf).upper(), 0.0)
        out.append({
            "control_id": cid,
            "decision": x["decision"],
            "evidence_ticket": str(x.get("evidence_ticket", "")),
            "evidence_control": str(x.get("evidence_control", "")),
            "confidence": confidence,
            "reason": str(x.get("reason", ""))[:1000],
        })
        seen.add(cid)
    return out


def hybrid_rank_controls_two_stage(case, llm, top_k=30, min_confidence=0.0, cap=None, uncertain_cap=None, evidence_mode="both", **kwargs):
    """
    Two-stage evidence verification approach.

    Stage 1: Broad candidate discovery (same prompt as hybrid_rank_controls).
    Stage 2: Per-candidate evidence verification — surface controls that pass
    evidence checks from the change ticket and control document.

    Args:
        evidence_mode: "both" requires evidence for AFFECTED and UNCERTAIN;
                      "uncertain_only" requires evidence only for UNCERTAIN
                      (keeps AFFECTED from stage 2 regardless of evidence).

    Returns same dict structure as hybrid_rank_controls, plus stage2_raw_response.
    """
    candidates = retrieve_control_documents(case, top_k)
    allowed = {d["control_id"] for d in candidates}
    baseline = rank_controls(case)
    baseline_ids = {x["control_id"] for x in baseline}

    # Stage 1: broad discovery
    prompt = build_prompt(case, candidates, baseline_ids)
    raw = llm(prompt) if callable(llm) else str(llm)

    parse_error = None
    try:
        recommendations = parse_recommendations(raw, allowed)
    except (ValueError, json.JSONDecodeError) as exc:
        recommendations = []
        parse_error = str(exc)

    # Collect AFFECTED and UNCERTAIN candidates for stage 2
    to_verify = [r for r in recommendations
                 if r.get("decision") in ("AFFECTED", "UNCERTAIN")
                 and r["control_id"] not in baseline_ids]

    # Stage 2: evidence verification
    stage2_parse_error = None
    if to_verify:
        verify_prompt = build_verification_prompt(case, to_verify, candidates, baseline_ids)
        raw2 = llm(verify_prompt) if callable(llm) else str(llm)
        try:
            verified = parse_verification_response(raw2, {r["control_id"] for r in to_verify})
        except (ValueError, json.JSONDecodeError) as exc:
            verified = []
            stage2_parse_error = str(exc)
    else:
        raw2 = ""
        verified = []

    # Build rec_by_id from verified results (stage 2 overrides stage 1)
    rec_by_id = {r["control_id"]: r for r in verified}

    # Only surface controls that pass verification WITH evidence from both sources
    llm_affected = set()
    llm_uncertain = set()
    llm_unaffected = set()
    llm_only_affected = []
    llm_only_uncertain = []

    for v in verified:
        cid = v["control_id"]
        decision = v.get("decision", "").upper()
        conf = v.get("confidence", 0.0)
        has_evidence = bool(v.get("evidence_ticket", "").strip()) and bool(v.get("evidence_control", "").strip())
        if decision == "AFFECTED":
            if evidence_mode == "both" and not has_evidence:
                llm_unaffected.add(cid)
                continue
            if conf >= min_confidence:
                llm_affected.add(cid)
            llm_only_affected.append((cid, conf))
        elif decision == "UNCERTAIN":
            if not has_evidence:
                llm_unaffected.add(cid)
                continue
            llm_uncertain.add(cid)
            llm_only_uncertain.append((cid, conf))
        else:
            llm_unaffected.add(cid)

    # Apply caps (same logic as hybrid_rank_controls)
    if cap is not None and llm_only_affected:
        llm_only_affected.sort(key=lambda x: (-x[1], x[0]))
        capped_ids = {cid for cid, _ in llm_only_affected[:cap]}
        llm_affected = {cid for cid in llm_affected if cid in baseline_ids or cid in capped_ids}

    if uncertain_cap is not None and llm_only_uncertain:
        llm_only_uncertain.sort(key=lambda x: (-x[1], x[0]))
        capped_uncertain_ids = {cid for cid, _ in llm_only_uncertain[:uncertain_cap]}
        demoted = {cid for cid in llm_uncertain if cid not in baseline_ids and cid not in capped_uncertain_ids}
        llm_uncertain = {cid for cid in llm_uncertain if cid in baseline_ids or cid in capped_uncertain_ids}
        llm_unaffected |= demoted

    recommended_ids = set(baseline_ids) | llm_affected
    uncertain_ids = sorted(llm_uncertain - baseline_ids)
    unaffected_ids = sorted(llm_unaffected)

    # Build audit rows
    changed_ids = set(case["change_ticket"].get("changed_entity_ids", []))
    vnodes = {n["id"]: n for n in case.get("visible_metadata", {}).get("nodes", [])}
    changed_names = [vnodes.get(nid, {}).get("name", "") for nid in changed_ids if nid in vnodes]
    changed_types = [vnodes.get(nid, {}).get("type", "") for nid in changed_ids if nid in vnodes]
    audit_rows = []
    all_ids = recommended_ids | set(uncertain_ids) | set(unaffected_ids)
    for cid in sorted(all_ids):
        rec = rec_by_id.get(cid, {})
        audit_rows.append({
            "control_id": cid,
            "baseline_flag": cid in baseline_ids,
            "raw_decision": rec.get("decision"),
            "confidence": rec.get("confidence"),
            "evidence_ticket": rec.get("evidence_ticket", ""),
            "evidence_control": rec.get("evidence_control", ""),
            "reason": rec.get("reason", ""),
            "changed_entity_ids": sorted(changed_ids),
            "changed_entity_names": changed_names,
            "changed_entity_types": changed_types,
            "final_class": "AFFECTED" if cid in recommended_ids else ("UNCERTAIN" if cid in uncertain_ids else "UNAFFECTED"),
            "surfaced_for_review": cid in recommended_ids or cid in llm_uncertain,
        })

    return {
        "baseline": baseline,
        "recommended_control_ids": sorted(recommended_ids),
        "uncertain_control_ids": uncertain_ids,
        "unaffected_control_ids": unaffected_ids,
        "llm_recommendations": verified,
        "parse_error": parse_error,
        "stage2_parse_error": stage2_parse_error,
        "raw_model_response": raw,
        "stage2_raw_response": raw2,
        "audit_rows": audit_rows,
    }

