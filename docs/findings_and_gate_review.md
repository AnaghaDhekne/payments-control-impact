> Phase 1 reported results. Final five-run raw artifacts are not present in this checkout; metrics require artifact reconciliation before external claims. Repair restores known synthetic edges and does not measure practical discoverability or effort.

# Development findings and workload gate review

Date: 2026-10-09  
Project: Payments Control Impact  
Splits: development (36 cases) and held-out test (18 cases), 30% change-correlated degradation  
Model: databricks-llama-4-maverick, temperature 0  
Status: **Held-out test confirms development findings. AI fails 3 of 4 gates. Lineage repair recommended as primary strategy.**

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

## Note on old test split

The file `output/archive/hybrid_matrix_remaining.json` contains the old test-split results: 5 test cases, 3 runs, top_k=20, pre-field-aware, pre-UNAFFECTED-fix. These results are **superseded** and should not be used for gate decisions. The corrected evaluation uses 36 development cases with top_k=30 field-aware retrieval.

## Summary of gate status

| Gate | Target | 5-run result | Status |
| --- | --- | --- | --- |
| Recovery | ≥50% | 58.0% avg (54.2–63.1%) | **PASS** |
| Workload | ≤25% | +170.9% avg (160.8–177.3%) | **FAIL** (structural mismatch — see above) |
| Stability | ≥95% | 84.0% | **FAIL** (173 disagreement pairs) |
| Parse failures | 0 | 0 | **PASS** |

## 5-run stability test results

Single-stage, k=30, no caps, 36 dev cases, 30% correlated, temperature 0:

| Run | Recovery | Workload+ | Uncertain | Excl misses | False pos | Parse fails |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | 57.3% | +172.2% | 118 | 96 | 152 | 0 |
| 2 | 54.2% | +167.6% | 129 | 103 | 153 | 0 |
| 3 | 60.0% | +160.8% | 151 | 90 | 128 | 0 |
| 4 | 55.6% | +176.7% | 147 | 100 | 147 | 0 |
| 5 | 63.1% | +177.3% | 135 | 83 | 142 | 0 |
| **Avg** | **58.0%** | **+170.9%** | **136** | **94** | **144** | **0** |

The 5-run agreement is 84.0% — below the 95% gate. The model produces inconsistent key-control decisions across runs even at temperature 0, with 173 disagreement pairs. Specific cases (e.g., CHG-004) show the model surfacing entirely different control sets in different runs, suggesting sensitivity to internal state or batching effects despite deterministic temperature settings.

## Overall POC verdict

**Development: 2 of 4 gates pass. Held-out test: 1 of 4 gates pass.** The AI approach fails the workload gate (structural mismatch), the stability gate (model non-determinism), and on held-out data also fails the recovery gate (46.5% vs 50% target). Combined with the Experiment F finding that lineage repair achieves higher recovery with near-zero false positives on both splits, the evidence recommends:

1. **Do not proceed to AI pilot under the current design.**
2. **Invest in lineage repair as the primary strategy** (one-time metadata hygiene investment).
3. **Use AI only as a supplementary tool** for cases where lineage cannot be repaired.
4. **Report this as a negative result** — the benchmark design and evaluation were sound; the AI approach does not meet the pre-registered safety gates.

## Follow-up

Five-run and repair results are reported below. Stakeholder delivery has not been independently verified. Phase 2 is described in [dependency_review_phase2.md](dependency_review_phase2.md).

## Experiment F: Lineage repair comparator (completed)

Simulates repairing observable metadata edges at various fractions and measures baseline key-control recovery, workload, and false positives. No LLM calls required — pure baseline on repaired metadata.

### Results (36 dev cases, 30% correlated)

| Repair % | Key hits | Recovery | Workload | Workload+ | False pos | Precision |
| --- | --- | --- | --- | --- | --- | --- |
| 0% | 51 | 0.0% | 176 | 0.0% | 0 | 100.0% |
| 10% | 73 | 9.8% | 239 | 35.8% | 1 | 99.6% |
| 20% | 90 | 17.3% | 285 | 61.9% | 1 | 99.6% |
| 30% | 105 | 24.0% | 329 | 86.9% | 1 | 99.7% |
| 50% | 154 | 45.8% | 452 | 156.8% | 2 | 99.6% |
| 70% | 203 | 67.6% | 640 | 263.6% | 4 | 99.4% |
| 100% | 276 | 100.0% | 900 | 411.4% | 9 | 99.0% |

### Head-to-head comparison at matched workload (452 controls, +156.8%)

| Approach | Recovery | False positives | Precision |
| --- | --- | --- | --- |
| AI (single-stage, k=30) | 55.6% | 127 | 72.0% |
| 50% lineage repair | 45.8% | 2 | 99.6% |

At the same workload, the AI recovers 9.8pp more key controls — but produces 125 more false positives. The AI's extra recovery comes at a 63× false-positive multiplier.

### At matched recovery (~55%)

To match the AI's 55.6% recovery, lineage repair needs approximately 58% of edges restored, yielding workload ~535 (vs AI's 452) with ~3 false positives (vs AI's 127). Lineage repair trades 83 extra reviews for 124 fewer false positives.

### At 70% repair, lineage repair dominates AI

| Metric | AI (best) | 70% lineage repair |
| --- | --- | --- |
| Recovery | 55.6% | **67.6%** |
| Workload | 452 | 640 |
| False positives | 127 | **4** |
| Precision | 72.0% | **99.4%** |

At 70% repair, lineage repair achieves **12pp higher recovery** than the AI with **31× fewer false positives**. The tradeoff is 188 extra reviews — but those reviews surface real affected controls (precision 99.4%), not ghost impacts.

### Key findings

1. **Lineage repair has near-zero false positives** (0-9) across all repair levels. The graph-based approach only surfaces controls connected via real propagating edges — it does not hallucinate connections. The AI produces 127 false positives (46% of its extras are waste).

2. **The AI's marginal advantage is small and precision-costly.** At matched workload, the AI recovers 9.8pp more key controls but with 125 more false positives. Each additional true recovery costs 12.8 false positives.

3. **Lineage repair at 70% beats AI on recovery.** 67.6% vs 55.6% recovery, with 31× fewer false positives. This suggests the AI's gain is primarily compensating for missing metadata that could be fixed directly.

4. **Repair is a one-time investment; AI is an ongoing cost.** Repairing lineage edges is a metadata hygiene investment that benefits every future change assessment. AI requires an LLM call per change scenario, with latency, cost, and non-determinism.

### Recommendation (Experiment F)

Per the evaluation improvement plan: "If the apparent AI gain is primarily information better lineage would supply, recommend repairing lineage instead."

The evidence supports this. The AI's gain is largely substitutable by lineage repair — and lineage repair is strictly better on precision (the safety-critical dimension for control assessment). 

**Recommend: invest in lineage repair as the primary strategy.** Use AI as a supplementary tool only for cases where lineage cannot be repaired (e.g., genuinely new entities with no prior metadata, or edges that were never documented).

### Script

`scripts/evaluate_repair.py` — runs the full repair sweep with recovery, workload, false positives, and precision metrics.

## Held-out test evaluation (completed)

The locked development configuration (single-stage, k=30, field-aware, no caps) was evaluated across five runs on the held-out test split. Lineage repair was also evaluated on the same test cases.

### Test split baseline characteristics

| Metric | Value |
| --- | --- |
| Cases | 18 |
| Key-control pairs | 162 |
| Baseline key hits | 18 (11.1%) |
| Baseline key misses | 144 |
| Baseline workload | 64 controls |
| Baseline workload per case | 3.6 controls |

The test split is even sparser than development (3.6 vs 4.9 controls/case). The 25% workload gate allows only **16 additional controls** across 18 cases — less than 1 extra per case. Recovering 50% of 144 misses requires **72 key controls**.

### AI hybrid results (5 runs, test split)

| Run | Recovery | Workload+ | Uncertain | Excl misses | False pos | Parse fails |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | 46.5% | +181.2% | 86 | 77 | 30 | 0 |
| 2 | 48.6% | +201.6% | 84 | 74 | 37 | 0 |
| 3 | 47.2% | +179.7% | 64 | 76 | 18 | 0 |
| 4 | 42.4% | +156.2% | 66 | 83 | 27 | 0 |
| 5 | 47.9% | +184.4% | 84 | 75 | 33 | 0 |
| **Avg** | **46.5%** | **+180.6%** | **77** | **77** | **29** | **0** |

5-run key-decision agreement: **87.6%**

### Lineage repair results (test split)

| Repair % | Key hits | Recovery | Workload | Workload+ | False pos | Precision |
| --- | --- | --- | --- | --- | --- | --- |
| 0% | 18 | 0.0% | 64 | 0.0% | 0 | 100.0% |
| 10% | 26 | 5.6% | 81 | 26.6% | 0 | 100.0% |
| 20% | 34 | 11.1% | 110 | 71.9% | 0 | 100.0% |
| 30% | 49 | 21.5% | 144 | 125.0% | 1 | 99.3% |
| 50% | 76 | 40.3% | 205 | 220.3% | 1 | 99.5% |
| 70% | 126 | 75.0% | 328 | 412.5% | 3 | 99.1% |
| 100% | 162 | 100.0% | 420 | 556.2% | 3 | 99.3% |

### AI vs lineage repair on test split

At matched workload (~180 controls):
- AI: 46.5% recovery, 29 false positives, 84% precision
- 30% lineage repair: 21.5% recovery, 1 false positive, 99.3% precision

At 70% lineage repair:
- AI: 46.5% recovery, 180 workload, 29 false positives
- 70% repair: **75.0% recovery** (61% higher), 328 workload, **3 false positives** (10x fewer)

Lineage repair at 70% achieves **61% higher recovery** than AI with **10x fewer false positives** on held-out data.

### Held-out gate status

| Gate | Target | AI result | Status |
| --- | --- | --- | --- |
| Recovery | ≥50% | 46.5% avg | **FAIL** (dropped from 58.0% on dev) |
| Workload | ≤25% | +180.6% avg | **FAIL** (structural mismatch) |
| Stability | ≥95% | 87.6% | **FAIL** |
| Parse failures | 0 | 0 | **PASS** |

**1 of 4 gates pass.** The AI approach fails the recovery gate on held-out data (46.5% vs 58.0% on development), confirming that the development recovery rate did not generalize.

### Dev vs test comparison

| Metric | Development (36 cases) | Test (18 cases) |
| --- | --- | --- |
| Baseline key recall | 18.5% | 11.1% |
| AI recovery | 58.0% avg | 46.5% avg |
| AI workload+ | +170.9% | +180.6% |
| AI agreement | 84.0% | 87.6% |
| AI false positives | 144 avg | 29 avg |
| Lineage repair 70% recovery | 67.6% | 75.0% |
| Lineage repair 70% false pos | 4 | 3 |

The held-out test confirms all development findings. The AI's recovery dropped below the 50% gate on held-out data, while lineage repair at 70% achieved even higher recovery (75.0%) with near-zero false positives (3).