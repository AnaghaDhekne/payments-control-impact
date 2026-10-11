> Historical Phase 1 document. Assumptions and plans may be superseded. Start with [the current README](../../README.md).

# Stakeholder Brief — Payments Control Impact POC Results

**Subject: POC complete — AI approach does not meet safety gates; lineage repair recommended**

## Bottom line

We tested whether an LLM can recover payment controls missed by degraded dependency graphs. **It cannot meet the pre-registered safety gates.** We recommend investing in **lineage repair** (fixing missing metadata) as the primary strategy instead.

## What happened

- Built a synthetic benchmark: 101 controls, 54 change scenarios, 30% lineage degradation
- The baseline (metadata-only graph) finds only 11-19% of affected key controls
- The AI (LLM-assisted narrative reasoning) recovers missed controls but:
  - **Fails the recovery gate** on held-out data (46.5% vs 50% target)
  - **Fails the workload gate** (+180% vs 25% limit — structurally infeasible)
  - **Fails the stability gate** (87.6% vs 95% — non-deterministic even at temperature 0)
  - Generates 29-144 false positives (up to 46% of its output is waste)

## The alternative: lineage repair

Fixing the missing dependency-graph edges instead of adding AI:

| Metric | AI (held-out test) | 70% lineage repair |
| --- | --- | --- |
| Key controls recovered | 46.5% | 75.0% |
| False positives | 29 | 3 |
| Precision | 84% | 99.1% |
| Reproducibility | 87.6% | 100% (deterministic) |

Lineage repair achieves **61% higher recovery** with **10x fewer false positives** and perfect determinism. It is a one-time investment that benefits every future change assessment.

## What we recommend

1. **Invest in lineage repair** — target 50-70% repair of degraded edges, prioritizing frequently changed entities
2. **Use AI only for edge cases** where lineage cannot be repaired (new entities, undocumented edges)
3. **Revisit the 25% workload gate** — it is arithmetically infeasible at this baseline sparsity
4. **Keep the benchmark** — the evaluation methodology is sound and reusable for future assessments

## Documents for review

| Document | Audience | Contents |
| --- | --- | --- |
| `docs/executive_summary_final.md` | Leadership | One-page summary with recommendation |
| `docs/findings_and_gate_review.md` | Technical team | Full report: all experiments, gate analysis, held-out test |
| `docs/archive/executive_review_pack.md` | Reviewers | Change Impact Review Pack template |
| `docs/evaluation_contract.md` | Audit | Pre-registered thresholds and benchmark design |

## Key numbers

- 36 development + 18 held-out test cases
- 5 runs per evaluation, temperature 0
- Model: databricks-llama-4-maverick
- Primary condition: 30% change-correlated degradation
- All code, tests, and data in the project repository

---
Prepared: 2026-10-09. All results from a synthetic benchmark. This is not production data.