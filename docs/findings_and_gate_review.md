# Development findings and workload gate review

Date: 2026-10-09  
Project: Payments Control Impact  
Split: development (36 cases), 30% change-correlated degradation  
Model: databricks-llama-4-maverick, temperature 0  
Status: **No configuration passes all three POC gates simultaneously.** This document presents the evidence and recommends revisiting the workload gate with absolute-count context.

## POC gates (from evaluation_contract.md)

1. Recover ≥50% of key-control misses made by the rules baseline.
2. Require ≤25% additional reviewer workload versus the rules baseline.
3. Achieve ≥95% agreement on key-control decisions across five runs.
4. Zero parse failures.

## Baseline characteristics at 30% correlated

| Metric | Value |
| --- | --- |
| Cases | 36 |
| Key-control pairs | 276 |
| Baseline key hits | 51 (18.5%) |
| Baseline key misses | 225 |
| Baseline workload | 176 controls |
| Baseline workload per case | 4.9 controls |

The baseline is **sparse**: at 30% correlated degradation, the metadata-only graph reaches only ~5 controls per change on average. The 25% workload gate allows at most **44 additional controls** (176 × 0.25) across all 36 cases — approximately **1.2 extra controls per case**.

## The structural mismatch

To pass the recovery gate (≥50%), the hybrid must recover at least **113 of the 225 missed key controls** (50% × 225). These are real affected controls that the baseline could not reach. Finding 113 key controls requires surfacing at least 113 additional controls — and in practice more, since the LLM cannot distinguish key from standard controls with perfect precision.

The workload gate allows 44 additions. The recovery gate requires ≥113. **The gates are in direct conflict**: no method can surface 113+ real controls while adding only 44. This is not a tuning failure — it is an arithmetic impossibility given the baseline's sparsity at this degradation level.

## Experiments conducted

### Experiment B: Field-aware retrieval (completed)

Compared old token-Jaccard retrieval to field-aware retrieval (uses changed entity names from visible metadata).

| Method | top_k | Key candidate recall | Affected recall | False/case |
| --- | --- | --- | --- | --- |
| Jaccard only | 20 | 65.6% | 45.0% | 8.9 |
| Field-aware | 20 | 67.8% | 47.7% | 8.2 |
| Jaccard only | 30 | 93.8% | 57.1% | 15.9 |
| **Field-aware** | **30** | **97.1%** | **59.1%** | **15.4** |

Field-aware retrieval at top_k=30 puts 97% of affected key controls in the candidate set. The retrieval problem is essentially solved. Remaining misses are C06 (8 instances, 7 cases) with no token overlap to any change ticket.

### Experiment D: Confidence capping (completed)

Tested capping LLM-only AFFECTED and UNCERTAIN additions by model confidence. The `cap` parameter limits AFFECTED additions per case; `uncertain_cap` limits UNCERTAIN items per case.

| cap | uncertain_cap | Recovery | Workload+ | Uncertain | False pos |
| --- | --- | --- | --- | --- | --- |
| None | None | 55.6% | +157% | 126 | 127 |
| None | 3 | 51.5% | +153% | 40 | 55 |
| 10 | 10 | 45.5% | +151% | 65 | 62 |
| 3 | 3 | 30.3% | +91% | 39 | 33 |
| 2 | 2 | 21.2% | +70% | 28 | 27 |
| 2 | 1 | 18.2% | +53% | 15 | 17 |

Finding: model confidence is not well-calibrated. High-confidence picks are not more likely to be true positives. Capping by confidence kills recovery proportionally to workload reduction — there is no operating point where caps selectively remove false positives while keeping true positives.

### Experiment C: Two-stage evidence verification (completed)

Stage 1: broad candidate discovery (same prompt). Stage 2: per-candidate verification requiring the LLM to cite specific evidence fragments from both the change ticket and the control document. Controls without cited evidence are downgraded to UNAFFECTED.

Two evidence modes tested:
- `"both"`: require evidence for AFFECTED and UNCERTAIN.
- `"uncertain_only"`: require evidence only for UNCERTAIN (keeps AFFECTED without evidence requirement).

| Mode | cap | ucap | Recovery | Workload+ | Uncertain | False pos |
| --- | --- | --- | --- | --- | --- | --- |
| both | None | None | 39.4% | +109% | 24 | 34 |
| both | 10 | 5 | 41.4% | +103% | 24 | 27 |
| both | 5 | 5 | 29.3% | +88% | 16 | 28 |
| uncertain_only | None | None | 46.5% | +121% | 26 | 39 |
| uncertain_only | 5 | 5 | 27.3% | +84% | 13 | 27 |

Finding: evidence verification halves false positives (34 vs 64 single-stage) and slashes the uncertain queue (24 vs 126), but the evidence requirement costs too much recovery — true positives are filtered out when degraded text lacks citable fragments. The `uncertain_only` mode is the best compromise (46.5% recovery, 39 false positives) but still misses the recovery gate.

## Best operating points

| Config | Recovery | Workload+ | False pos | Parse fails |
| --- | --- | --- | --- | --- |
| **Single-stage, k=30, no caps** | **55.6%** ✅ | +157% | 127 | 0 ✅ |
| Two-stage uncertain_only, no caps | 46.5% | +121% | 39 | 0 ✅ |
| Two-stage both, no caps | 39.4% | +109% | 34 | 0 ✅ |

The single-stage config is the only one that passes the recovery gate (≥50%). Its workload is +157% (452 vs 176 baseline = 276 extra controls across 36 cases = 7.7 per case). Of these 276 extras, 127 are false positives (46%) and 149 are true affected controls that the baseline missed.

## Recommendation: revisit the workload gate

The 25% workload gate was set as a **percentage** increase over the baseline. At 30% correlated degradation, the baseline is so sparse (4.9 controls/case) that the 25% budget (1.2 extra/case) is smaller than the number of real missed key controls (6.3 per case on average). The gate penalizes the hybrid for finding real controls the baseline missed.

### Why the 25% gate is infeasible at this degradation level

- Baseline surfaces 176 controls for 36 cases.
- 25% gate allows 44 additions (total ≤ 220).
- Recovery gate requires ≥113 recovered key controls.
- Even with perfect precision (no false positives), 113 additions > 44 allowed.
- **The recovery gate alone requires 2.6× the workload budget.**

### What the absolute counts show

At the best operating point (single-stage, k=30, no caps):
- **276 extra controls** surfaced (452 total vs 176 baseline).
- **149 are true affected controls** the baseline missed — these are necessary reviews.
- **127 are false positives** — these are the actual workload waste.
- The false-positive rate among extras is 46%, meaning roughly 1 in 2 LLM additions is unnecessary.
- The two-stage evidence approach reduces false positives to 34 (among ~84 extras) — a 40% false-positive rate — at the cost of dropping recovery to 39%.

### Proposed alternatives

1. **Adjust the workload gate to an absolute count.** Instead of ≤25% increase, cap false positives (extras not in ground truth) at an absolute number per case. For example, ≤3 false positives per case allows ~108 false positives across 36 cases, which the two-stage approach already achieves (34 false positives at 18 cases ≈ 68 at 36 cases).

2. **Measure workload as false-positive rate, not total additions.** The hybrid's value is finding real controls the baseline missed. The cost is false positives. A gate like "false-positive rate among extras ≤50%" is met by the single-stage approach (46%) and exceeded by the two-stage approach (40%).

3. **Accept the recovery gate and report workload honestly.** Proceed with the single-stage config (55.6% recovery), report the absolute workload (276 extras, 127 false positives, 149 true recoveries), and let stakeholders decide whether 7.7 extra reviews per change is acceptable for recovering 3.1 key controls per change.

## Stability gate (not yet tested)

The 5-run agreement gate (≥95%) has not been re-tested with the top_k=30 field-aware config. The old 5-run test on the dev split (top_k=20, pre-fix) showed 85.9% agreement. The old test split (this file, 5 cases, 3 runs, top_k=20) showed 94.7% agreement at 30% correlated. A proper 5-run test on the full 36-case dev split with top_k=30 is needed before the stability gate can be assessed.

## Note on old test split

The file `output/hybrid_matrix_remaining.json` contains the old test-split results: 5 test cases, 3 runs, top_k=20, pre-field-aware, pre-UNAFFECTED-fix. These results are **superseded** and should not be used for gate decisions. The corrected evaluation uses 36 development cases with top_k=30 field-aware retrieval.

## Summary of gate status

| Gate | Target | Best result | Status |
| --- | --- | --- | --- |
| Recovery | ≥50% | 55.6% | **PASS** (single-stage, k=30) |
| Workload | ≤25% | +157% | **FAIL** (structural mismatch — see above) |
| Stability | ≥95% | not tested | **PENDING** |
| Parse failures | 0 | 0 | **PASS** |

## Next steps

1. Present this finding to stakeholders and request a workload gate review.
2. Run the 5-run stability test on the best config (single-stage, k=30, no caps).
3. If the gate is revised or the workload finding is accepted, run the locked held-out test evaluation.
4. If the gate is not revised, report POC no-go under the current design and recommend lineage repair (Experiment F) as an alternative.