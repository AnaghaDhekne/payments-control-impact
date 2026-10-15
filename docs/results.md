# Results

## Current: detective agent, live development runs (2026-10-14/15)

| Setting | Value |
|---|---|
| Model | `databricks-gpt-oss-120b`, temperature 0 (0.3 on empty-answer retries) |
| Budget | 60 investigation steps per case, plus one verifier call per non-UNAFFECTED finding |
| Condition | 30% change-correlated degradation, development split |
| Runs | 1 per case |
| Labels | Computed offline by `run_detective_suite`; never sent to the model |

| Case | Change | Affected / key | Rules flagged | Key misses | Recovered | New true / false | Uncertain | Step errors |
|---|---|---|---|---|---|---|---|---|
| CHG-001 | Debtor town-name mapping | 49 / 19 | 0 | 19 | 14 | 30 / 5 | 19 | 0 of 59 |
| CHG-014 | Authorization exception report | 10 / 0 | 6 | 0 | – | 4 / 0 | 0 | 0 |
| CHG-025 | Outbound message mapping | 20 / 5 | 6 | 3 | 3 | 4 / 0 | 20 | 0 of 50 |
| CHG-017 | Settlement-status feed | 30 / 5 | 7 | 5 | 5 | 18 / 0 | 2 | 1 of 52 |
| **Total** | | | **19** | **27** | **22 (81.5%)** | **56 / 5 (91.8%)** | **41** | |

### Against the gates

| Gate | Target | Observed | Status |
|---|---|---|---|
| Key-miss recovery | ≥ 50% | 81.5% (22 of 27) | Met on development cases |
| Added reviewer workload | ≤ 25% | 102 added review items (56 true, 5 false, 41 uncertain) vs 19 rules items | Not met |
| Consistency over 5 runs | ≥ 95% | — | Not measured |

### Caveats

- **Not held-out evidence.** All four cases were inspected while the agent was
  being fixed. Four cases is also a small sample.
- **Review burden.** 41 UNCERTAIN items, 20 of them on CHG-025, mostly where
  the agent and verifier disagree. This is the main open problem. See also
  the gate tension in [evaluation.md](evaluation.md).
- **Coverage.** CHG-025 stopped at step 50 with 10 controls undecided; they are
  reported as uninvestigated. In CHG-017 the agent once requested nonexistent
  control IDs; the tool rejected them and the run continued.
- **CHG-014** is the case where the baseline already reaches every key
  control. The agent added 4 controls, all truly affected, and no false flags.

### Before and after the fixes (CHG-001)

| Run | Recovered key misses | Investigation step errors | Cause |
|---|---|---|---|
| Before | 0 of 19 | 56 of 60 | gpt-oss content blocks discarded; prompt and budget too large |
| After | 14 of 19 | 0 of 59 | See robustness measures in [architecture.md](architecture.md) |

### Raw artifacts

Not in Git (they contain full prompts). On the Databricks workspace:

- CHG-001: workspace folder `output/runs/detective-suite-08/run1/`
- CHG-014, CHG-025, CHG-017:
  `/Volumes/workspace/default/detective_runs/suite-09/run1/`, job run
  `823235726063295`

Inspect with `python -m scripts.inspect_detective_run <path>/<case>.json`.

## Pre-registered: frozen check on unseen development cases (2026-10-15)

Registered before running. Code, prompts and model are frozen at commit
`bb6d945` (the commit before this note); nothing is changed between cases.

- **Cases:** CHG-004, CHG-002, CHG-041, CHG-026, CHG-029, CHG-016, CHG-049,
  CHG-010. None of their change templates were inspected while fixing the
  agent (each template has three near-identical releases; siblings of
  CHG-001, CHG-014, CHG-025 and CHG-017 were excluded).
- **Size:** 49 key misses by the rules baseline (19, 19, 2, 2, 3, 2, 2, 0);
  CHG-010 has none and checks for false flags.
- **Same settings** as above: `databricks-gpt-oss-120b`, 60 steps, one run,
  30% change-correlated, output `/Volumes/workspace/default/detective_runs/suite-10`.
- **Reading the result:** pooled key-miss recovery, new-control precision,
  UNCERTAIN count and uninvestigated count, reported in full whatever they are.
  A large drop from the 81.5% above would suggest the earlier result relied on
  the tuned cases or on the benchmark's control-family structure.

## Diagnosis: where UNCERTAIN comes from (CHG-025, consistency run 1)

Of 21 UNCERTAIN items, 20 were proposer AFFECTED / verifier not AFFECTED.
Checked against the answer key for four of them: the proposer was wrong on
three (C01, C08, C09: outbound message mapping does not reach validation or
reconciliation controls) and the verifier correctly withheld approval. The
fourth (C06, truly affected) was a bug: the verifier agreed on retry but
returned `counter_evidence: null`, which failed validation; fixed in
`d6ca2e4`. Conclusion so far: the review burden comes mainly from the
proposer over-claiming impact across functional areas; the verifier is
protecting precision. Reducing it means a more conservative proposer, to be
tested only on fresh cases.

## Next steps

1. Analyse the CHG-025 proposer/verifier disagreements before changing prompts.
2. Decide and document how the workload gate treats correct recoveries.
3. Run 5 repeats on the same cases to measure consistency.
4. Freeze code, prompts and model; run the remaining development cases, then
   the test split once.
5. Have a payments or controls practitioner review a sample of AFFECTED and
   UNCERTAIN findings.

## Earlier phases (archived)

Raw files are in [archive/](../archive/README.md). The code and documents that
produced them are on the branch `pre-cleanup-2026-10-15`.

**Phase 1, hybrid retrieval and ranking** (2026-10-08, `databricks-llama-4-maverick`,
36 development cases, 5 runs): 49.5% key-miss recovery, +201.5% reviewer
workload, 85.9% five-run agreement. Did not pass the gates.

**Phase 2, dependency-edge proposals** (2026-10-13, GPT OSS 120B, 5-run union
ensemble, 18 held-out cases): 57.6% key-miss recovery and 91.2% precision on
affected controls, but only 25.3% of proposed direct edges were correct, and
the pipeline included an automatic quote-correction step. A simulated
LLM-as-reviewer study on the same proposals gave 5.6% recovery and 27.3%
precision. The impact result and the reviewed-edge result measure different
things, and neither established a reproducible agentic workflow, which led to
the current detective design.
