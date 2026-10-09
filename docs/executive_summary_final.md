# Executive Summary — Payments Control Impact POC

Date: 2026-10-09  
Status: **POC complete. Held-out test confirms: 1 of 4 gates pass. Not recommended for AI pilot.**  
Splits: development (36 cases) and held-out test (18 cases), 30% change-correlated degradation  
Model: databricks-llama-4-maverick, temperature 0, top_k=30 field-aware retrieval  
Full report: [findings_and_gate_review.md](findings_and_gate_review.md)

## Recommendation

**Invest in lineage repair as the primary strategy. Use AI as a supplementary tool only where lineage cannot be repaired.**

The AI approach recovers missed key controls but fails three safety gates on held-out data: recovery drops below 50%, workload far exceeds the limit, and decisions are inconsistent across repeated runs. Lineage repair — restoring missing dependency-graph edges — achieves 75% recovery with 3 false positives and perfect determinism on the same held-out cases.

## What we tested

A synthetic benchmark of 101 payment controls and 54 change scenarios. At 30% change-correlated degradation, 30% of dependency-graph edges near changed entities are removed, simulating stale lineage metadata. The baseline (metadata-only graph traversal) finds only 18.5% of affected key controls.

We tested whether an LLM can recover missed controls by reasoning over narrative documents (change tickets and control descriptions). Four experiments were conducted on the development split:

- **Experiment B**: Field-aware retrieval (candidate discovery)
- **Experiment C**: Two-stage evidence verification (require cited evidence)
- **Experiment D**: Confidence-based capping (rank and limit LLM additions)
- **Experiment F**: Lineage repair comparator (fix metadata instead of adding AI)

## Results against pre-registered gates

| Gate | Target | AI result | Lineage repair (70%) | Status |
| --- | --- | --- | --- | --- |
| Recovery | 50% | Dev: 58.0% PASS / Test: 46.5% FAIL | Repair test: 75.0% PASS |
| Workload | 25% | Dev: +170.9% FAIL / Test: +180.6% FAIL | Repair test: +412.5% FAIL |
| Stability | 95% | Dev: 84.0% FAIL / Test: 87.6% FAIL | Repair: 100% PASS |
| Parse failures | 0 | 0 PASS | N/A |

The workload gate is structurally infeasible at this degradation level: the baseline surfaces only ~5 controls per change, so the 25% budget allows just ~1 extra control per change — but recovering 50% of missed key controls requires finding ~3.5 per change. See the full report for the arithmetic.

## AI vs lineage repair at matched workload

At the same reviewer workload (452 controls):

| Metric | AI approach | 50% lineage repair |
| --- | --- | --- |
| Key controls recovered | 55.6% | 45.8% |
| False positives | 127 | 2 |
| Precision | 72.0% | 99.6% |

The AI recovers 10pp more key controls — but generates 63× more false positives. Each additional true recovery costs 12.8 false positives.

At 70% lineage repair (held-out test data), the comparison flips entirely:

| Metric | AI (test avg) | 70% lineage repair |
| --- | --- | --- |
| Recovery | 46.5% | **75.0%** |
| False positives | 29 | **3** |
| Precision | 84% | **99.1%** |
| Determinism | 87.6% agreement | **100%** |

Lineage repair achieves 61% higher recovery, 10x fewer false positives, and perfect determinism on held-out data.

## Why lineage repair wins

1. **Precision**: The graph only surfaces controls connected via real propagating edges. It does not hallucinate connections. The AI produces 127–153 false positives (46% of its extras are waste).

2. **Determinism**: Lineage repair is deterministic — the same input always produces the same output. The AI is non-deterministic even at temperature 0, with 173 key-control decisions changing across 5 runs.

3. **One-time vs ongoing cost**: Repairing lineage edges is a metadata hygiene investment that benefits every future change assessment. AI requires an LLM call per change scenario, with latency, cost, and non-determinism.

4. **Safety**: In control assessment, false positives waste reviewer time but false negatives miss real impacts. Lineage repair's near-zero false positives mean reviewers focus on real risks. The AI's 46% false-positive rate erodes trust in its output.

## What AI still offers

AI provides value in scenarios where lineage **cannot** be repaired:
- Genuinely new entities with no prior metadata
- Edges that were never documented
- Controls referenced only in narrative text, not in structured lineage

In these cases, AI-assisted narrative reasoning can surface candidates that graph traversal cannot. But this is a supplementary tool, not a replacement for metadata hygiene.

## What we recommend

1. **Prioritize lineage repair**: Invest in metadata hygiene to restore missing/stale dependency edges, particularly near frequently changed entities. Target 50–70% repair of currently degraded edges.

2. **Use AI for edge cases only**: Deploy AI-assisted narrative reasoning for changes involving new entities, undocumented edges, or controls with no structured lineage. Require evidence citation for each AI recommendation.

3. **Report as negative result**: The AI approach does not meet the pre-registered safety gates. The benchmark and evaluation methodology are sound and reusable for future assessments.

4. **Revisit the workload gate**: The 25% workload gate is infeasible at this baseline sparsity. Consider alternative formulations (absolute false-positive cap, precision threshold, or workload normalized to missed-key-count rather than baseline workload).

## Supporting documents

| Document | Contents |
| --- | --- |
| [findings_and_gate_review.md](findings_and_gate_review.md) | Full technical findings, all experiments, gate analysis |
| [executive_delivery_focus.md](executive_delivery_focus.md) | Project positioning and implementation path |
| [evaluation_contract.md](evaluation_contract.md) | Pre-registered thresholds and benchmark design |
| [evaluation_improvement_plan.md](evaluation_improvement_plan.md) | Experiment plan (A–F) |
| [executive_review_pack.md](executive_review_pack.md) | Change Impact Review Pack template |

All results are from a synthetic benchmark (development + held-out test split). This is not production data.