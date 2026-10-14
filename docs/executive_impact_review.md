# Executive Impact Review — Payments Control Impact

**Date:** 2026-10-14  
**Benchmark:** 101 payment controls, 54 change scenarios, synthetic  
**Evaluation:** 18 held-out test cases, 30% change-correlated degradation  
**Review mode:** Oracle adjudication (human review pending)  

---

## Recommendation

**Invest in lineage repair as the primary strategy. Use AI as a
supplementary tool only where lineage cannot be repaired.**

Lineage repair recovers **75% of missed critical controls** with **99.1%
precision** and perfect determinism — a one-time metadata investment that
benefits every future change assessment. The AI system recovers **57.6%**
with **91.2% precision** but requires per-change LLM calls, introduces
non-determinism, and has not been validated with human reviewers.

Three findings drive this recommendation:  
1. Lineage repair dominates on every dimension executives care about  
2. AI adds value only where lineage cannot be repaired  
3. Human review is the gating step before any production deployment  

---

## Finding 1: Lineage repair dominates on every executive dimension

### The problem

When dependency metadata degrades by 30% (change-correlated), the
metadata-only baseline finds just **11.1% of critical payment controls** —
89% are missed. At 60% degradation, recall drops to 7.4%.

### What lineage repair achieves

| Repair investment | Key controls recovered | Missed controls remaining | False positives | Precision |
| --- | --- | --- | --- | --- |
| 0% (status quo) | 11.1% | 89.0% | 0 | 100% |
| 30% of edges repaired | 30.2% | 69.8% | 1 | 99.3% |
| 50% of edges repaired | 46.9% | 53.1% | 1 | 99.5% |
| **70% of edges repaired** | **77.8%** | **22.2%** | **3** | **99.1%** |
| 100% (full repair) | 100% | 0% | 3 | 99.3% |

**Key insight:** Repairing 70% of degraded edges recovers 75% of missed
critical controls. The remaining 25% may require AI or manual discovery.

### What the AI system achieves (same 18 test cases)

| Dimension | Lineage repair (70%) | AI Phase 2 (held-out) | AI Phase 1 (held-out) |
| --- | --- | --- | --- |
| Key control recovery | **75.0%** | 57.6% | 46.5% |
| Precision | **99.1%** | 91.2% | 84.0% |
| False positives | **3** | 8 | 29 |
| Determinism | **100%** | ~100% (5-run ensemble) | 87.6% |
| Cost model | One-time metadata fix | LLM call per change | LLM call per change |
| Gate status (Phase 2) | N/A | **2 of 2 PASS** | N/A |
| Gate status (Phase 1) | 3 of 4 | N/A | 1 of 4 |

### Why lineage repair wins for executives

1. **Safety:** 3 false positives vs 8-29 for AI. In payment controls, false
   positives waste reviewer time but false negatives miss real impacts.
   Lineage repair's near-zero false positives mean reviewers focus on real
   risks.
2. **Cost:** One-time investment vs ongoing per-change LLM cost. Every future
   change benefits from the same repair.
3. **Trust:** Deterministic output. The same input always produces the same
   result. AI is non-deterministic even at temperature 0 (Phase 1: 87.6%
   agreement across 5 runs).
4. **Simplicity:** No model endpoint, no latency, no quota dependencies.
   Works offline.

---

## Finding 2: AI adds value only where lineage cannot be repaired

### Where AI succeeds

The AI system (GPT OSS 120B, two-stage evidence proposals, 5-run ensemble)
**passes both Phase 2 safety gates** on held-out data:

| Gate | Target | Result | Status |
| --- | --- | --- | --- |
| Key-miss recovery | >= 50% | 57.6% (83/144) | **PASS** |
| Control precision | >= 80% | 91.2% (83/91) | **PASS** |

Per-case analysis shows real signal: **6 of 18 cases achieve 100% recovery**
with perfect precision. The AI finds controls that lineage repair cannot —
particularly for changes involving new entities or narrative-only references.

### Where AI falls short

| Limitation | Impact |
| --- | --- |
| Oracle-adjudicated, not human-reviewed | Real reviewers may reject correct edges or approve incorrect ones. 91.2% precision is an upper bound. |
| Edge-level precision is 25.3% | The AI proposes correct *controls* but wrong *edges*. It surfaces the right controls via indirect paths. |
| 1 case (CHG-006) has 0% recovery | 7 key controls missed, none recovered. AI has blind spots. |
| 2 cases have < 60% precision | CHG-024 (50%), CHG-042 (20%) — false positives erode trust. |
| Model non-determinism at temp 0 | Phase 1 showed 87.6% agreement; Phase 2 stabilized via 5-run ensemble but individual runs vary. |

### The complementary strategy

| Scenario | Recommended approach | Rationale |
| --- | --- | --- |
| Stale metadata, edges once existed | **Lineage repair** | Restore known edges; deterministic, high precision |
| New entities, no prior metadata | **AI-assisted discovery** | AI can infer dependencies from narrative documents |
| Edges referenced only in text | **AI-assisted discovery** | Graph traversal cannot find text-only references |
| Broadly-impactful changes (19 key misses) | **Lineage repair first** | AI recovers 0% on these cases in Phase 1; repair recovers 47% at 50% |

---

## Finding 3: Human review is the gating step before production

### Current state

All results use **oracle adjudication** — comparing AI proposals against the
hidden ground-truth graph. This represents an **upper bound** on performance.
Real human reviewers will likely have:
- Lower precision (rejecting correct edges)
- Higher false positive rates (approving incorrect edges)
- Variable accuracy across reviewers
- Time cost per review (not yet measured)

### What must happen before pilot

| Step | Why | Status |
| --- | --- | --- |
| Blinded human review of proposals | Measure real reviewer precision vs oracle | Not started |
| Reviewer time per proposal | Quantify actual workload | Not started |
| Adversarial cases | Test stale narratives, legacy names, no-overlap scenarios | Not started |
| Audit trail validation | Case-version integrity, rollback of mistaken edges | Not started |
| Pilot stop rule | Escalation path for uncertain controls, human sign-off | Not started |

### Decision framework

```
IF human review precision >= 80% AND reviewer time <= 5 min/proposal
    THEN proceed to limited pilot with lineage repair as primary
ELIF human review precision < 80%
    THEN investigate reviewer training or workflow redesign
ELSE
    THEN AI is not ready for pilot; invest in lineage repair only
```

---

## Assumptions and boundaries

| Assumption | Validation | Risk if wrong |
| --- | --- | --- |
| Synthetic benchmark reflects real payment controls | Architecture reviewed, domain-modeled | Real controls may have different structure/complexity |
| 30% correlated degradation is representative | Calibrated with domain expert | Real degradation may be higher or lower |
| Oracle adjudication approximates human review | Industry standard for POC | Human reviewers behave differently than oracle |
| 5-run ensemble stabilizes non-determinism | Measured: ~100% Phase 2, 87.6% Phase 1 | More runs may be needed for production |
| Jaccard threshold (0.05) generalizes | Tuned on dev data, validated on held-out | May need recalibration on real data |
| Observable-only pipeline (no label leakage) | Audited + unit tested | Confirmed: no leakage found |

---

## Cost comparison

| Dimension | Lineage repair (70%) | AI Phase 2 |
| --- | --- | --- |
| One-time cost | Repair 70% of degraded edges | Prompt engineering, pipeline development |
| Per-change cost | $0 (deterministic graph traversal) | 5 LLM calls per change (ensemble) |
| Latency | Instant (graph traversal) | Minutes (5 model calls + ensemble) |
| Maintenance | Edge hygiene (ongoing metadata quality) | Model endpoint availability, prompt updates |
| Scalability | Limited to graph coverage | Scales with LLM context window |

---

## Phase 1 context (for comparison)

Phase 1 tested LLM-based control ranking (not edge repair). It **fails 3 of 4
gates** on held-out data:

| Gate | Target | Result | Status |
| --- | --- | --- | --- |
| Recovery | >= 50% | 46.5% | FAIL |
| Workload increase | <= 25% | +180.6% | FAIL |
| 5-run agreement | >= 95% | 87.6% | FAIL |
| Parse failures | 0 | 0 | PASS |

The workload gate is **structurally infeasible** at this degradation level:
the baseline surfaces ~3.6 controls per change, so 25% allows only ~1 extra
control, but recovering 50% of missed key controls requires finding ~4 per
change. No configuration across all experiments passes both recovery and
workload gates simultaneously.

---

## Source data

| Artifact | Location | Produces |
| --- | --- | --- |
| evaluate_baseline.py | scripts/ | Baseline recall, workload, per-case results |
| evaluate_repair.py | scripts/ | Lineage repair comparator (0-100% repair) |
| dependency_proposals.py | scripts/ | Phase 2 LLM edge proposals with evidence |
| hybrid.py | scripts/ | Phase 1 ranking, retrieval, filtering |
| evaluate_hybrid.py | scripts/ | Phase 1 evaluation harness |
| heldout_results.json | output/heldout_run/ | Held-out evaluation results (18 cases) |
| final_report.md | docs/ | Full project report with gate analysis |

All numbers in this document are reproducible from the frozen pipeline.
See the [runbook](runbook.md) for commands and the [evaluation contract](evaluation_contract.md)
for pre-registered thresholds.
