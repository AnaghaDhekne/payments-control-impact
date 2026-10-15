# Detective path: live development results (2026-10-14/15)

First live runs of the tool-using detective (`scripts/detective.py`) on
Databricks after the fixes listed in [detective_recovery.md](detective_recovery.md).
These are **development-split results on cases inspected while fixing the
code**. They are not held-out results and must not be presented as such.

## Configuration

| Setting | Value |
|---|---|
| Model endpoint | `databricks-gpt-oss-120b`, temperature 0 (0.3 on empty-answer retries) |
| Agent budget | 60 investigation steps per case, plus one verifier call per non-UNAFFECTED finding |
| Condition | 30% change-correlated degradation, development split |
| Code | `main` at `9a16f02` (CHG-001) and `6be2cab` (other cases); logic identical for scoring |
| Runs per case | 1 (consistency across runs not yet measured) |
| Labels | computed offline by `run_detective_suite`; never sent to the model |

## Results

| Case | Change | Affected / key | Baseline flagged | Key misses | Recovered | New true / false | Uncertain | Step errors |
|---|---|---|---|---|---|---|---|---|
| CHG-001 | Debtor town-name mapping | 49 / 19 | 0 | 19 | 14 | 30 / 5 | 19 | 0 of 59 |
| CHG-014 | Authorization exception report | 10 / 0 | 6 | 0 | n/a | 4 / 0 | 0 | 0 |
| CHG-025 | Outbound message mapping | 20 / 5 | 6 | 3 | 3 | 4 / 0 | 20 | 0 of 50 |
| CHG-017 | Settlement-status feed | 30 / 5 | 7 | 5 | 5 | 18 / 0 | 2 | 1 of 52 |
| **Total** | | | **19** | **27** | **22 (81.5%)** | **56 / 5 (91.8%)** | **41** | |

CHG-025 finished at step 50 with 10 controls undecided; these are reported as
uninvestigated, not as unaffected. In CHG-017 the agent once requested
nonexistent control IDs (C49–C56); the tool rejected them and the run
continued.

## Against the frozen decision gates

| Gate | Target | Observed | Status |
|---|---|---|---|
| Key-miss recovery | >= 50% | 81.5% (22/27) | Met on development cases |
| Added reviewer workload | <= 25% vs rules | 19 baseline items vs 102 added review items (56 true, 5 false, 41 uncertain) | Not met |
| Key-control consistency over 5 runs | >= 95% | Not measured | Open |

As noted in `detective_recovery.md`, the workload gate counts correct
recoveries as workload, so on this benchmark any method meeting the recovery
gate exceeds it. The actionable problem is the 41 UNCERTAIN items, mostly
proposer/verifier disagreement (20 in CHG-025 alone). The gates are reported
here unchanged; they were not loosened after seeing results.

## Before comparison (same case, CHG-001)

| Run | Recovered key misses | Investigation step errors |
|---|---|---|
| suite-01 (before fixes) | 0 of 19 | 56 of 60 |
| suite-08 (after fixes) | 14 of 19 | 0 of 59 |

## Next steps

1. Reduce UNCERTAIN volume: analyse the CHG-025 disagreements before changing
   any prompt.
2. Measure consistency: `--runs 5` on the same cases.
3. Freeze code and prompts, then evaluate on development cases not inspected
   during fixing, and finally on the held-out split.
4. Practitioner review of a sample of AFFECTED and UNCERTAIN findings.

## Raw artifacts

Per-case results, traces and model calls are on the Databricks volume:

- CHG-001: workspace folder `output/runs/detective-suite-08/run1/`
- CHG-014, CHG-025, CHG-017: `/Volumes/workspace/default/detective_runs/suite-09/run1/`
  (job run `823235726063295`)

Inspect any of them with
`python -m scripts.inspect_detective_run <path>/CHG-xxx.json`.
