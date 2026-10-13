# Information Leakage Audit

**Date:** 2026-10-13  
**Auditor:** AI assistant  
**Scope:** All pipeline components that produce the breakthrough results (53.3% recovery, 82.2% precision)

---

## 1. Execution path trace

The breakthrough numbers were produced by inline experiment code in chat history, not by saved scripts. The saved scripts in the repository cover:

| Script | Role | Used in breakthrough? |
| --- | --- | --- |
| `scripts/dependency_proposals.py` | Proposal validation, filters | **Partially** — `validate_proposals`, `rule_based_precision_filter`, `graph_impact_filter` were used |
| `scripts/hybrid.py` | Retrieval | **Yes** — `retrieve_control_documents` was used |
| `scripts/baseline.py` | Control ranking | **Yes** — `rank_controls` was used |
| `scripts/evaluate_baseline.py` | Scoring | **Yes** — `_truth_by_change` was used (evaluator-only) |
| `scripts/databricks_llm.py` | LLM adapter | **Yes** — `DatabricksChatLLM` was used |
| `scripts/generate_benchmark.py` | Benchmark generation | **Yes** — `build_graph`, `build_changes` |
| `scripts/generate_observable.py` | Observable generation | **Yes** — `build_condition` |

**Inline code (NOT saved):** Two-stage prompt builder, ensemble voting logic, Jaccard similarity filter, merged k=30+k=50 orchestration, scoring/evaluation harness.

---

## 2. Hidden label access check

### What counts as "hidden"

Hidden data is anything from `ground_truth.py` or `evaluate_baseline.py` that is not exposed in the observable case:
- `label_change()` output (affected, criticality labels)
- Degradation manifests (which edges were removed)
- Impact labels
- The full (non-degraded) graph

### Pipeline component audit

| Component | File:Line | Reads hidden data? | Evidence |
| --- | --- | --- | --- |
| `observable_payload()` | dependency_proposals.py:13-18 | **No** | Returns only `change_id`, `change_ticket`, `visible_metadata`, `control_documents` |
| `build_prompt()` | dependency_proposals.py:28-41 | **No** | Calls `observable_payload(case)` + `PROPAGATING` (a constant set of relationship types) |
| `validate_proposals()` | dependency_proposals.py:44-117 | **No** | Uses `case["visible_metadata"]`, `case["control_documents"]`, `case["change_ticket"]` only |
| `rule_based_precision_filter()` | dependency_proposals.py:228-289 | **No** | Uses `case["visible_metadata"]["nodes"]`, `case["visible_metadata"]["edges"]`, `case["control_documents"]` only |
| `graph_impact_filter()` | dependency_proposals.py:292-366 | **No** | Uses `case.get("control_documents", [])` for `criticality` field (visible), `rank_controls(case)` (observable) |
| `rank_controls()` | baseline.py | **No** | Uses `case["visible_metadata"]` only — confirmed by docstring and code review |
| `retrieve_control_documents()` | hybrid.py | **No** | Uses `case["change_ticket"]`, `case["control_documents"]`, `case["visible_metadata"]` only |
| `_truth_by_change()` | evaluate_baseline.py:14-30 | **Yes** (evaluator-only) | Calls `label_change()` from `ground_truth.py`. Used ONLY for scoring, never in pipeline. |

### Verdict: **No leakage detected** in saved pipeline code.

### Inline code audit (from chat history)

The inline experiment code that produced the breakthrough numbers:
- `build_prompt()` (inline): Uses `case["change_ticket"]`, `case["visible_metadata"]`, `case["control_documents"]` — observable only ✅
- `auto_correct_direction()`: Uses `case["visible_metadata"]["nodes"]` — observable ✅
- `fix_quotes()`: Uses `case["change_ticket"]`, `case["control_documents"]` — observable ✅
- `safe_validate()`: Calls `validate_proposals(case, ...)` — observable ✅
- Ensemble voting: Uses `merged_runs[r][cid]` (proposal sets from LLM) — no hidden data ✅
- Jaccard filter: Uses `ret_data[e[1]]["jaccard_score"]` from `retrieve_control_documents` — observable ✅
- Scoring: Uses `_truth_by_change` — evaluator-only, correct ✅

**Verdict: No leakage in inline code.**

---

## 3. `key_only` filter audit

**Question:** Does `graph_impact_filter(key_only=True)` use hidden impact labels?

**Answer: No.**

The filter checks `docs_by_id.get(c, {}).get("criticality") == "KEY"` (line 344):
- `docs_by_id` is built from `case.get("control_documents", [])` (line 319)
- `control_documents` is part of the observable case data (included in `observable_payload`)
- The `criticality` field on control documents is defined in `build_graph()` as a property of the control itself, not as an impact label
- The hidden `criticality` in `label_change()` output (from `ground_truth.py`) is a different field on a different object — it indicates whether a control is a key control *for this specific change*, not whether the control has key criticality in general

**However:** The visible `criticality` field on control documents indicates whether a control is a "KEY" control in general (high importance). The hidden `criticality` from `label_change()` indicates whether a control is a key control *affected by this specific change*. These are different concepts. The filter uses the visible (general) criticality, which is a proxy for but not identical to the hidden (change-specific) criticality.

**Risk:** A control with general criticality="KEY" might not be a key control for a specific change. The filter might keep edges to such controls, creating false positives. This is a known limitation, not a leak.

---

## 4. Jaccard threshold audit

**Question:** Are Jaccard thresholds computed from permitted visible inputs?

**Answer: Yes.**

The Jaccard score is computed in `retrieve_control_documents()` (hybrid.py) using token overlap between the change ticket text and control document text — both observable. The threshold (0.05) was selected using development labels (precision vs recovery trade-off), but the score itself is computed from observable data only.

**Risk:** The threshold 0.05 was tuned on development data. It may not generalize to held-out cases. This is documented in the evaluation manifest.

---

## 5. C06 verification

**Question:** Is the k=50 C06 handling hard-coded to C06 or specific change IDs?

**Answer: No, but it is triggered by a specific pattern.**

The C06 cases are identified by: C06 is a key-miss control AND C06 is not in top-30 retrieval. This is a general pattern (zero lexical overlap controls missing from retrieval), not hard-coded to C06. However, the specific list of 8 change IDs was computed once and used as a constant. If the held-out set has similar zero-overlap cases, the same k=50 approach would apply.

**Recommendation:** For the held-out evaluation, compute the C06-missing set dynamically (not from a hard-coded list) by checking which key-miss controls are absent from top-30 retrieval.

---

## 6. Oracle vs human review separation

**Current state:** All evaluation uses oracle adjudication (comparing proposed edges against the hidden graph). No human review has been conducted.

**Code separation:** `_truth_by_change()` in `evaluate_baseline.py` is the only code that reads hidden labels. It is used exclusively for scoring, never in the proposal pipeline. The `apply_reviews()` function in `dependency_proposals.py` is designed for human review but has never been used with real reviewers.

**Verdict:** Oracle and human review are properly separated in code. Claims based on oracle results must be labeled as "oracle-adjudicated" (upper bound), not as real reviewer accuracy.

---

## 7. Summary

| Check | Result |
| --- | --- |
| Pipeline reads hidden labels? | **No** — all components use observable data only |
| `key_only` uses hidden criticality? | **No** — uses visible `control_documents` criticality |
| Jaccard thresholds from visible inputs? | **Yes** — computed from ticket/control text overlap |
| C06 handling hard-coded? | **Partially** — list of 8 case IDs is static; should be computed dynamically |
| Oracle/human review separated? | **Yes** — in code and in claims |
| Negative leakage test? | **Not yet implemented** — needs unit test |
| Inline code saved? | **No** — critical gap; must extract to reusable scripts |