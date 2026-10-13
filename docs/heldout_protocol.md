# Held-out Evaluation Protocol

**Status:** FROZEN as of 2026-10-13. No changes after this point without creating a new protocol version.

---

## 1. Dataset

| Property | Value |
| --- | --- |
| Benchmark | 101 controls, 54 change scenarios |
| Split | 36 development, 18 held-out test |
| Split method | `build_condition(level=30, mode="correlated")` assigns `split` field |
| Degradation | 30% correlated edge removal |
| Test period | 2026-10-01 to 2027-03-31 |
| Key control definition | `affected=True AND criticality="KEY"` from `label_change()` |

**Independence check:** Development and test cases share the same 101-control benchmark graph but have different change scenarios. No change scenario appears in both splits. Near-duplicate narratives have not been formally checked — recommend manual review before evaluation.

---

## 2. Primary outcomes (predeclared)

### Recovery

**Definition:** Key misses recovered / baseline key misses, pooled across all test cases.

- Numerator: count of key-miss controls (key controls not in baseline ranking) that appear in the post-repair ranking
- Denominator: count of key-miss controls across all test cases
- Zero-denominator handling: if a case has 0 key misses, it contributes 0 to both numerator and denominator
- Per-case vs pooled: **pooled** (sum across all cases, then divide)
- Gate: **>= 50%**

### Precision (control-level)

**Definition:** True newly-recommended controls / all newly-recommended controls, pooled.

- Numerator: newly-recommended controls (in post-repair but not in baseline) that are truly affected
- Denominator: all newly-recommended controls
- "Truly affected" determined by `label_change()` (hidden ground truth, evaluator-only)
- Gate: **>= 80%**

**Also report (secondary, not gated):**
- Edge-level precision: proposed edges matching hidden graph / all proposed edges
- False-positive controls: newly-recommended controls that are not affected
- False-positive edges: proposed edges not in hidden graph
- Total reviews: number of proposals requiring human review

---

## 3. Gates (predeclared)

### Phase 2 provisional gates

| Gate | Target | Metric |
| --- | --- | --- |
| Key-miss recovery | >= 50% | Pooled key-miss recovery |
| Reviewed proposal precision | >= 80% | Control-level precision (pooled) |
| Zero incorrect approved edges | 0 | Edge-level: no approved edge that is not in hidden graph |
| Reviews per recovered key | <= 3 | Total proposals / recovered key controls |

**Reporting:** Each gate reported as PASS / FAIL / NOT TESTED. Do not claim overall success unless all 4 gates pass. If 2 of 4 pass, report as "2 of 4 gates met" — do not claim overall success.

### Phase 1 original gates (for comparison)

| Gate | Target |
| --- | --- |
| Recovery | >= 50% |
| Workload increase | <= 25% |
| 5-run agreement | >= 95% |
| Parse failures | 0 |

---

## 4. Pipeline configuration (frozen)

| Setting | Value | Tuned on dev? |
| --- | --- | --- |
| Model | databricks-gpt-oss-120b | No |
| Temperature | 0 | No |
| Max tokens | 8000 | No |
| Runs per case | 5 | No |
| Retrieval k (standard) | 30 | No |
| Retrieval k (zero-overlap cases) | 50 | Yes (dev data) |
| Ensemble threshold | >=1 vote (union) | No |
| Retrieval score min | 0.01 | Yes (dev data) |
| Jaccard tier 1 threshold | >= 0.05 | Yes (dev data) |
| Jaccard tier 2 threshold | >= 0.045 AND votes >= 3 | Yes (dev data) |
| Rule-based filter | Enabled | No |
| Graph-impact filter key_only | True | Yes (dev data) |

**No post-test tuning.** If the held-out evaluation fails, improvements must be labeled as a new experiment with a fresh untouched test set.

---

## 5. Stability calculation

- 5 independent runs per case at temperature 0
- Agreement: for each proposed edge, count in how many of 5 runs it appears. Report distribution.
- 5-run agreement metric: fraction of edges that appear in all 5 runs (>=5/5) / all proposed edges (>=1/5)
- Gate: not formally set for Phase 2; report descriptively

---

## 6. Baselines for comparison

| Baseline | Description |
| --- | --- |
| Metadata-only | `rank_controls(case)` on degraded graph, no repair |
| Phase 1 AI (original) | Llama 4 Maverick control ranking |
| Phase 2 AI (original) | Llama 4 Maverick evidence-backed proposals |
| Lineage repair (50%) | Restore 50% of removed edges |
| Lineage repair (70%) | Restore 70% of removed edges |
| Improved Phase 2 | GPT OSS 120B two-stage + ensemble + filters |

All baselines evaluated on the same 18 held-out test cases with the same scoring code.

---

## 7. Pass/fail reporting and uncertainty

- Report each gate individually: PASS / FAIL / NOT TESTED
- Provide per-case breakdown: case ID, key misses, recovered, new controls, affected new, precision, recovery
- Bootstrap 95% confidence intervals for recovery and precision (1000 resamples)
- Rule-of-three bound if zero incorrect approved edges are observed: 3/n upper bound
- Break down by degradation mechanism (random vs correlated) and level (0/30/60%) if applicable
- Report any parse failures, abstentions, and excluded controls separately

---

## 8. Execution checklist

1. Confirm model endpoint access and quotas
2. Compute the zero-overlap case list dynamically (not from hard-coded list)
3. Run 5-run k=30 ensemble on all 18 test cases
4. Run 5-run k=50 ensemble on zero-overlap test cases
5. Save ALL raw responses, proposals, votes, and filtered outputs to workspace files (not /tmp)
6. Apply frozen pipeline configuration (no changes)
7. Score using `_truth_by_change` (evaluator-only)
8. Report all gates, per-case breakdown, and confidence intervals
9. Commit raw outputs, scored results, and protocol to git
10. Do NOT modify the frozen run if gates fail — investigate and create a new experiment