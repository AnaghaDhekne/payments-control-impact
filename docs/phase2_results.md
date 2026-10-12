# Phase 2 Evaluation Results

Date: 2026-10-11
Model: databricks-llama-4-maverick (temperature=0, max_tokens=6000)
Split: development (36 cases)
Degradation: 30% correlated
Review mode: oracle adjudication (approve edges present in hidden graph, reject absent)

## Summary

The evidence-backed dependency proposal workflow was evaluated across all 36
development cases with live LLM calls and oracle-adjudicated reviews. The system
fails 3 of 4 provisional Phase 2 gates. Only the "zero incorrect approved edges"
gate passes, which is trivially guaranteed by oracle review.

| Gate | Threshold | Result | Status |
| --- | --- | --- | --- |
| Key-miss recovery | >= 50% | 3.6% | FAIL |
| Reviewed proposal precision | >= 80% | 21.3% | FAIL |
| Zero incorrect approved edges | 0 | 0 | PASS |
| Reviews per recovered key | <= 3 | 9.4 | FAIL |

## Aggregate Metrics (single run, 36 dev cases)

- Total proposals (post-validation): 75
- Total validation rejections: 58
- Correct proposals (edge in hidden graph): 16
- Reviewed proposal precision: 21.3%
- Total key misses: 225
- Recovered key misses: 8
- Key-miss recovery rate: 3.6%
- False positive controls: 0
- Incorrect approved edges: 0 (oracle review)
- Final control reviews: 187

## 5-Run Stability (36 dev cases)

Proposal counts and correctness vary significantly across runs:

| Run | Total proposals | Correct proposals |
| --- | --- | --- |
| 1 | 68 | 11 |
| 2 | 71 | 14 |
| 3 | 79 | 15 |
| 4 | 71 | 18 |
| 5 | 67 | 8 |

- 5-run proposal agreement: 20.6% (29/141 edge pairs consistent across all runs)
- The model is highly non-deterministic at temperature 0; proposed edges change
  substantially between runs for the same case.

## Per-Case Breakdown (single run)

| Change ID | Proposals | Correct | Key misses | Recovered | Recovery |
| --- | --- | --- | --- | --- | --- |
| CHG-004 | 2 | 0 | 19 | 0 | 0% |
| CHG-014 | 1 | 0 | 0 | 0 | N/A |
| CHG-010 | 3 | 0 | 0 | 0 | N/A |
| CHG-025 | 4 | 3 | 3 | 2 | 67% |
| CHG-022 | 0 | 0 | 19 | 0 | 0% |
| CHG-041 | 1 | 0 | 2 | 0 | 0% |
| CHG-026 | 1 | 0 | 2 | 0 | 0% |
| CHG-028 | 4 | 0 | 0 | 0 | N/A |
| CHG-017 | 0 | 0 | 5 | 0 | 0% |
| CHG-029 | 8 | 0 | 3 | 0 | 0% |
| CHG-002 | 2 | 0 | 19 | 0 | 0% |
| CHG-044 | 1 | 0 | 2 | 0 | 0% |
| CHG-043 | 1 | 0 | 1 | 0 | 0% |
| CHG-038 | 0 | 0 | 19 | 0 | 0% |
| CHG-050 | 1 | 0 | 0 | 0 | N/A |
| CHG-047 | 1 | 0 | 3 | 0 | 0% |
| CHG-032 | 1 | 0 | 0 | 0 | N/A |
| CHG-016 | 3 | 3 | 2 | 2 | 100% |
| CHG-020 | 5 | 0 | 19 | 0 | 0% |
| CHG-049 | 4 | 0 | 2 | 0 | 0% |
| CHG-052 | 3 | 3 | 1 | 1 | 100% |
| CHG-034 | 0 | 0 | 2 | 0 | 0% |
| CHG-035 | 0 | 0 | 5 | 0 | 0% |
| CHG-011 | 3 | 3 | 2 | 1 | 50% |
| CHG-008 | 1 | 0 | 3 | 0 | 0% |
| CHG-013 | 4 | 4 | 3 | 2 | 67% |
| CHG-001 | 2 | 0 | 19 | 0 | 0% |
| CHG-031 | 2 | 0 | 2 | 0 | 0% |
| CHG-007 | 1 | 0 | 1 | 0 | 0% |
| CHG-037 | 0 | 0 | 19 | 0 | 0% |
| CHG-046 | 1 | 0 | 0 | 0 | N/A |
| CHG-040 | 2 | 0 | 19 | 0 | 0% |
| CHG-019 | 5 | 0 | 19 | 0 | 0% |
| CHG-005 | 2 | 0 | 2 | 0 | 0% |
| CHG-023 | 6 | 0 | 3 | 0 | 0% |
| CHG-053 | 0 | 0 | 5 | 0 | 0% |

Only 5 of 36 cases produced any correct proposals: CHG-025, CHG-016,
CHG-052, CHG-011, CHG-013. The remaining 31 cases produced zero correct
proposals, meaning the LLM either abstained, proposed edges not in the
hidden graph, or had all proposals rejected by validation.

## Failure Mode Analysis

### 1. Prompt bias toward DEPENDS_ON

The prompt's JSON example hardcodes `"relationship": "DEPENDS_ON"`, causing
the model to overwhelmingly propose DEPENDS_ON edges. But the removed edges
that cause key misses span three relationship types:

| Relationship | Needed (first 10 cases) | Proposed | Correct |
| --- | --- | --- | --- |
| GOVERNED_BY | 29 | 2 | 1 |
| DEPENDS_ON | 34 | 17 | 6 |
| EVIDENCES | 7 | 1 | 0 |

The model proposes mostly DEPENDS_ON but misses the majority of GOVERNED_BY
and EVIDENCES edges, which account for 36 of 70 needed edges.

### 2. Too few proposals

The model proposes ~2 edges per case on average, but cases average ~7 removed
edges leading to key misses. Even with perfect precision, 2 proposals cannot
recover 7 missing edges. The model abstains too aggressively.

### 3. Low precision on proposed edges

Of 75 accepted proposals, only 16 (21.3%) match edges in the hidden graph.
The remaining 59 propose edges that do not exist in the ground truth. The
model fabricates direct dependencies that are not supported by the graph.

### 4. High non-determinism

5-run agreement is 20.6%, meaning the model proposes different edges nearly
every run for the same case. This makes the workflow unreliable: a reviewer
cannot expect consistent proposals across evaluations.

### 5. Cases with 19 key misses get zero recovery

8 cases have 19 key misses each (152 total). The model recovered 0 of these.
These cases involve changes to data elements (D03, D04, D08) with broad
downstream impact. The model fails to propose the many edges needed to
restore reachability for broadly-impactful changes.

## Comparison to Phase 1

Phase 1 (control ranking, top_k=30, 5 runs, dev split):
- Recovery: 58.0% (PASS 50% gate)
- Workload: +170.9% (FAIL 25% gate)
- Stability: 84.0% (FAIL 95% gate)

Phase 2 (dependency proposals, oracle review, dev split):
- Recovery: 3.6% (FAIL 50% gate)
- Precision: 21.3% (FAIL 80% gate)
- Stability: 20.6%
- Incorrect approved edges: 0 (PASS, oracle-guaranteed)

Phase 2 recovery is dramatically worse than Phase 1 (3.6% vs 58.0%). The
dependency-proposal approach recovers far fewer key misses because the model
proposes too few edges and most are incorrect. Phase 1's ranking approach,
while failing the workload gate, at least surfaces relevant controls.

## Limitations

1. Oracle review is not human review. Real human reviewers may reject correct
   edges (false negatives) or approve incorrect ones (false positives). Oracle
   review represents an upper bound on recovery given the model's proposals.
2. Only one model tested (databricks-llama-4-maverick). Other models may perform
   differently.
3. No human-without-AI comparison conducted. The doc requires comparing against
   a human reviewing the same documents without AI.
4. Test split not yet evaluated. These results are development-split only.
5. The prompt includes all 101 control documents (~72K chars per case). A
   smaller, targeted document set may improve precision.

## Conclusion

Phase 2 evidence-backed dependency proposals fail the development evaluation.
The system cannot reliably identify missing dependency edges from observable
metadata and control documents. The model proposes too few edges, with low
precision, and high non-determinism. Lineage repair (Phase 1's simulated
comparator, 75% recovery at 70% repair) remains the dominant strategy.

No success claim is warranted. The original negative results from Phase 1
remain valid for the original configuration.
