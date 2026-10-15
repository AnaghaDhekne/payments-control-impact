# Evaluation

## Question

At 30% change-correlated metadata degradation, does the detective recover
enough of the key controls that the rules baseline misses, without an
unacceptable review burden and with stable decisions? If not, the POC
recommends fixing lineage metadata instead of piloting an AI workflow.

## Metrics (per case, pooled across cases)

Computed by `scripts/score_detective.py` from a saved result and offline labels
`{affected_control_ids, key_control_ids}`:

| Metric | Definition |
|---|---|
| Key misses | Affected key controls not reached by the rules baseline |
| Key recovered | Key misses that end up in `recommended_control_ids` |
| Key-miss recovery | Key recovered ÷ key misses |
| New true / new false | Recommended controls outside the baseline that are / are not affected |
| New-control precision | New true ÷ (new true + new false) |
| Uncertain | Controls sent to human review; workload, never counted as recovered |
| Review items | New recommendations ∪ uncertain |
| Uncertain true | UNCERTAIN controls that are affected |
| Uninvestigated | Controls with no decision; reported, never counted as safe |

`run_detective_suite.py` pools counts across cases (micro-average) and, with
`--runs N`, writes `consistency.json`: the share of affected key-control pairs
given the same recommend / not-recommend decision in every run.

## Decision gates (pre-registered, unchanged)

At 30% change-correlated degradation, proceed to a pilot only if the detective:

1. recovers **at least 50%** of key-control misses made by the rules baseline;
2. adds **at most 25%** reviewer workload compared with the rules baseline;
3. reaches **at least 95%** agreement on key-control decisions across five runs.

Report sample size and uncertainty. With zero observed key misses among n
pairs, report the approximate 95% upper bound on the miss rate as 3/n.

### Known tension between gates 1 and 2

On the development split the baseline flags 176 controls and misses 225
affected key controls. Recovering 50% means adding at least 113 controls,
+64% workload even at perfect precision. Because correct recoveries count as
workload, any method that passes gate 1 fails gate 2 on this benchmark, and
where the baseline flags nothing (for example CHG-001) any review item is an
unbounded increase.

**Decision (registered 2026-10-15, before the frozen-check results):** gate 2
stays exactly as written and is reported as met or not met. Counting only
wrong flags and UNCERTAIN items was considered and rejected as a replacement:
on the four tuned cases it gives 46 items against 19 (+242%), so it would not
change the verdict, and redefining a gate until it passes is not credible.
Review burden is additionally described, never gated, by:

| Measure | Definition |
|---|---|
| Avoidable review items | Items beyond the baseline (new recommendations ∪ UNCERTAIN) that are not affected |
| Avoidable items per case | Avoidable review items ÷ cases |
| Review-queue true share | Affected items ÷ all items beyond the baseline |

On the four tuned cases: 102 items beyond the baseline, of which 56 new
recommendations are affected and 5 are not; how many of the 41 UNCERTAIN
items are affected was not recorded by that code version, so the true share is
between 55% and 95%.

## Kill conditions

Do not recommend a pilot if the gates fail, if key-control decisions are
materially inconsistent across runs, if a qualified payments or controls
reviewer finds the dependency model unrealistic, or if healthy metadata makes
deterministic selection sufficient.

## Hygiene

- Labels are computed offline and never sent to the model; tests enforce it.
- Development cases used while fixing the agent are **not** evidence of
  held-out performance.
- Before a final evaluation: freeze code, prompts and model; run development
  cases not inspected during fixing; then the 18 test cases once.
- The earlier Phase 2 held-out run inspected the test cases during diagnosis;
  a final evaluation should use fresh scenario families or be reported with
  that caveat.
- Keep every run, including failures. Do not regenerate hard cases after
  failures.

## Reference: rules baseline by condition

Development split (36 cases, 891 affected pairs, 276 key pairs):

| Condition | Key-control recall | Key pairs missed | Controls flagged |
|---|---|---|---|
| 0% | 100% | 0 | 900 |
| 30% correlated | 18.5% | 225 | 176 |
| 60% correlated | 12.0% | 243 | 101 |

Test split (18 cases, 417 affected pairs, 162 key pairs): 100% / 11.1% / 7.4%
key-control recall at 0% / 30% / 60% correlated (144 and 150 key pairs missed).

Regenerate with `python -m scripts.evaluate_baseline`.
