# Change Impact Review Pack — Payments Control Impact

Date: 2026-10-08
Source: output/dev_30_correlated.json (36 development cases, 5 runs, 30% correlated degradation)
Status: Development benchmark data — not production findings. Use for methodology evaluation only.

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

The hybrid approach sends the change ticket, baseline hits, and top-20
candidate control documents to the LLM for narrative reasoning.

| Metric | Value (5-run average) |
| --- | --- |
| Final key hits (AFFECTED + UNCERTAIN) | 162 (58.8%) |
| Recovered key misses | 111 (49.5% of 225) |
| AFFECTED + UNCERTAIN workload | 531 controls |
| UNCERTAIN queue | 242 controls |
| False positives | 160 controls |
| Parse failures | 0 |

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
| Excluded key misses | 114 | Key controls never surfaced by baseline or LLM. 41% residual miss rate. |
| False positives | 160 | Controls surfaced as AFFECTED/UNCERTAIN but not actually affected per ground truth. |
| UNCERTAIN queue | 242 | Controls with ambiguous evidence requiring manual investigation. |
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
- Hybrid (AFFECTED + UNCERTAIN): 531 controls (3.0x baseline)
- POC gate threshold: <= 220 controls (25% increase over 176)
- Current workload is 2.4x over the gate threshold

## 6. Decision Note

### POC Gate Assessment

| Gate | Threshold | Result | Status |
| --- | --- | --- | --- |
| Recovery | >= 50% | 49.5% | FAIL (borderline) |
| Workload | <= 25% | 201.5% | FAIL (severe) |
| Agreement | >= 95% | 85.9% | FAIL |
| Parse failures | = 0 | 0 | PASS |

**Verdict: NOT ready for pilot under current design.**

### What to Investigate

1. Why are 114 key controls never surfaced? Candidate retrieval (Jaccard
token overlap) is not finding them in the top-20. Field-aware retrieval
(changed entity name matching) has been implemented but not yet evaluated.

2. Why are 160 false positives generated? The LLM may be over-classifying
controls as AFFECTED when narrative evidence is weak. Evidence-grounded
classification (requiring cited fragments) may reduce this.

3. Why is agreement only 85.9%? The LLM gives different answers on 14% of
key-control decisions across runs, even at temperature 0. Alternate models
or 2-call intersection may improve stability.

### What Metadata to Repair

The root cause of baseline misses is degraded lineage. Repairing observable
dependency edges near changed entities would directly improve baseline recall
without adding LLM workload. The lineage repair comparator (Experiment F)
will quantify whether fixing metadata is more effective than adding AI.

### Does AI-Assisted Review Offer Net Value?

At current configuration: **marginal, not sufficient.** The LLM recovers
111 key controls but at the cost of 355 additional controls to review.
The recovery rate (49.5%) is borderline. The workload (201.5%) is
unsustainable. However, the review pack itself is useful regardless —
it surfaces known impacts, potential impacts, and evidence gaps that a
reviewer can act on even when the LLM performance gates fail.

### Next Steps

1. Evaluate field-aware retrieval (implemented, not yet tested)
2. Run Experiment D: rank/cap LLM additions by confidence
3. Run Experiment F: lineage repair comparator
4. Run Experiment E: alternate models for stability
5. Lock best development configuration
6. Run held-out test split ONCE as confirmation

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

Source: development benchmark data from output/dev_30_correlated.json, 2026-10-08.
This is synthetic benchmark data, not production findings.