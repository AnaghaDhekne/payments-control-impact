# Change Impact Review Pack — Payments Control Impact

Date: 2026-10-09  
Source: 5-run stability test (36 development cases, 30% correlated degradation, top_k=30 field-aware)  
Status: POC complete: 2 of 4 gates pass. Not recommended for AI pilot. See executive_summary_final.md.

## 1. Change Summary

The benchmark models 36 payment modernization changes across 10 process steps
(instruction, validation, sanctions screening, fraud/limits, authorization,
transformation, dispatch, acknowledgements, reconciliation, reporting).

Changes span:
- Structured address/field mappings
- Validation rule modifications
- Transaction limit adjustments
- Interface and message format changes
- System decommissions and aliases/renames
- Control automation parameter changes
- Rollback scenarios
- Cosmetic/no-impact changes (adversarial)

At 30% correlated degradation, the dependency graph has 30% of its edges
removed, concentrated near the changed entities, simulating locally stale
lineage metadata.

## 2. Known Impacts (Baseline — Graph-Reachable Controls)

The deterministic baseline traverses visible dependency edges from changed
entities to reachable controls.

| Metric | Value |
| --- | --- |
| Key control pairs | 276 |
| Baseline key hits | 51 (18.5%) |
| Baseline key misses | 225 (81.5%) |
| Baseline workload | 176 controls |

Interpretation: The degraded dependency graph reaches only 18.5% of key
controls. 225 key-control pairs are missed because graph edges connecting
them to the changed entity have been removed. These are evidence gaps, not
confirmed misses — the controls may still be affected.

## 3. Additional Potential Impacts (LLM-Suggested)

The hybrid approach sends the change ticket, baseline hits, and top-30
field-aware candidate control documents to the LLM for narrative reasoning.

| Metric | Value (5-run average) |
| --- | --- |
| Final key hits (AFFECTED + UNCERTAIN) | ~182 (65.6%) |
| Recovered key misses | ~131 (58.0% of 225) |
| AFFECTED + UNCERTAIN workload | ~477 controls |
| UNCERTAIN queue | 136 controls |
| False positives | 144 controls |
| Parse failures | 0 |
| 5-run key-decision agreement | 84.0% |

Output classification:
- AFFECTED: LLM identified narrative evidence of impact. Included in
  positive recommendations alongside baseline.
- UNCERTAIN: LLM found partial or ambiguous evidence. Surfaced in a
  separate review queue. Counted toward workload. Not suppressed.
- UNAFFECTED: LLM assessed no impact. Not surfaced. Tracked for audit.

All LLM-suggested controls are marked UNVERIFIED. They require human
review before any compliance action is taken.

## 4. Evidence Gaps

| Gap Type | Count | Description |
| --- | --- | --- |
| Excluded key misses | 94 | Key controls never surfaced by baseline or LLM. 34% residual miss rate. |
| False positives | 144 | Controls surfaced as AFFECTED/UNCERTAIN but not actually affected per ground truth. |
| UNCERTAIN queue | 136 | Controls with ambiguous evidence requiring manual investigation. |
| 5-run disagreements | 173 | Key-control decisions that change across repeated runs at temperature 0. |
| Graph degradation | 30% | Edges removed near changed entities. Missing lineage is the root cause of baseline misses. |

Key distinction: A missing graph edge is NOT proof that a control is
unaffected. It is an evidence gap requiring investigation. The 114 excluded
key misses represent controls where neither the graph nor the LLM provided
sufficient evidence to surface them.

## 5. Prioritized Review Queue

Priority ordering for reviewers:

1. KEY controls in baseline (51) — highest confidence, graph-reachable.
   Action: Confirm impact, assess design adequacy.

2. KEY controls recovered by LLM as AFFECTED (~111) — narrative evidence
   supports impact. Action: Verify evidence, assess control design.

3. KEY controls in UNCERTAIN queue — partial evidence. Action: Investigate
   manually, request additional documentation.

4. STANDARD controls in AFFECTED set — lower priority but still surfaced.
   Action: Batch review after key controls are cleared.

5. STANDARD controls in UNCERTAIN queue — lowest priority. Action: Review
   if capacity allows; document as unresolved otherwise.

Review burden:
- Baseline only: 176 controls
- Hybrid (AFFECTED + UNCERTAIN): ~477 controls (2.7x baseline)
- POC gate threshold: 220 controls (25% increase over 176)
- Current workload is 2.2x over the gate threshold
- Lineage repair at 50%: 452 controls, 45.8% recovery, 2 false positives
- Lineage repair at 70%: 640 controls, 67.6% recovery, 4 false positives

## 6. Decision Note

### POC Gate Assessment

| Gate | Threshold | Result | Status |
| --- | --- | --- | --- |
| Recovery | >= 50% | 58.0% avg | **PASS** |
| Workload | <= 25% | +170.9% avg | **FAIL** (structural mismatch) |
| Agreement | >= 95% | 84.0% | **FAIL** (173 disagreements) |
| Parse failures | = 0 | 0 | **PASS** |

**Verdict: 2 of 4 gates pass. NOT ready for AI pilot under current design.**

### Lineage Repair Comparison (Experiment F)

At the same reviewer workload (452 controls), lineage repair at 50%
recovers 45.8% of missed key controls with only 2 false positives
(precision 99.6%). The AI recovers 58.0% but with 144 false positives
(precision 72%).

At 70% lineage repair, recovery exceeds AI (67.6% vs 58.0%) with 4 false
positives (vs 144) and perfect determinism (vs 84% agreement).

**Recommendation: invest in lineage repair as the primary strategy.**
Use AI only for cases where lineage cannot be repaired (new entities,
undocumented edges, narrative-only controls).

### What to Investigate

1. **Workload gate feasibility**: The 25% gate is arithmetically
infeasible at this baseline sparsity. Stakeholders should consider
alternative formulations (see findings_and_gate_review.md).

2. **Model non-determinism**: The LLM gives different answers on 16%
of key-control decisions across runs, even at temperature 0.

3. **Lineage repair priorities**: Which edges to repair first -
concentrate on frequently changed entities and their incident
relationships.

### Next Steps

1. Present findings to stakeholders for workload gate review
2. If gate revised: run locked held-out test evaluation
3. If gate not revised: report POC no-go and invest in lineage repair
4. See executive_summary_final.md for the stakeholder summary

## Acceptance Criteria Check

- [x] Reproducible development results (36 cases, 5 runs, valid JSON)
- [x] Per-control trace from change to candidate impact (audit rows)
- [x] Separate known, potential and unknown impact categories (Sections 2-4)
- [x] No suppression of uncertain items (UNCERTAIN queue counted)
- [x] Reviewer can take concrete actions from output (Section 5)

## See Also

- [Executive Delivery Focus](executive_delivery_focus.md) — project positioning and implementation path
- [Evaluation Improvement Plan](evaluation_improvement_plan.md) — pre-registered thresholds and experiments
- [Industry Comparison](industry_comparison.md) — vendor-by-vendor comparison with citations
- [Novelty Pitch](novelty_pitch.md) — one-page stakeholder pitch
- [Project Reference](project_reference.md) — plain-language summary of all components
- [Result Summary & Actions](../output/result_summary_and_actions.txt) — full metrics report

Source: 5-run stability test, 2026-10-09. Synthetic benchmark data.