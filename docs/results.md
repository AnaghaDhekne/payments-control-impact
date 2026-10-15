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

**Result (job `211771677628591`, completed 2026-10-15 15:10 CT):**

| Case | Change | Key misses | Recovered | New true / false | Uncertain |
|---|---|---|---|---|---|
| CHG-004 | Creditor country-code mapping | 19 | 11 | 22 / 0 | 19 |
| CHG-002 | Debtor country-code mapping | 19 | 16 | 34 / 2 | 11 |
| CHG-041 | Structured-address validation rule | 2 | 2 | 3 / 0 | 1 |
| CHG-016 | Transformation service | 2 | 2 | 4 / 1 | 21 |
| CHG-049 | Reconciliation report | 2 | 1 | 6 / 0 | 1 |
| CHG-026 | High-value approval threshold | 2 | 0 | 0 / 0 | 10 |
| CHG-029 | Screening exception report | 3 | 0 | 0 / 0 | 1 |
| CHG-010 | Outbound network interface | 0 | – | 10 / 5 | 18 |
| **Total** | | **49** | **32 (65.3%)** | **79 / 8 (90.8%)** | **82** |

Recovery gate met (65.3% ≥ 50%), lower than the 81.5% on tuned cases, as the
pre-registered reading anticipated. Workload gate not met (169 added review
items vs 38 rules items). 2 controls uninvestigated. Precision stable at about
90%. CHG-002 was briefly also resumed by a mistakenly submitted second job
(cancelled within minutes); the original job rewrote the case file from its own
state afterwards, and the file carries no resume marker.

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

**Frozen-check misses (CHG-026, CHG-029), checked against the answer key.**
The opposite failure also occurs. On CHG-026 (high-value approval threshold)
the proposer correctly marked C04 ("payments exceeding configured thresholds
require enhanced authorization", key) and C05 AFFECTED, but the verifier
returned UNCERTAIN for lack of a graph chain although the text link is direct.
On CHG-029 the verifier correctly marked C03 (key) AFFECTED but the proposer
had said UNCERTAIN, so the disagreement went to review. Family members C041,
C030 and C032 (key, affected) were marked UNAFFECTED by the proposer and,
because UNAFFECTED is never verified, received no second look. Errors
therefore run in both directions: over-claiming across functional areas
(CHG-025) and a verifier too strict on text-evident links plus unverified
UNAFFECTED decisions (CHG-026, CHG-029). Version B addresses only the first
and may lower recovery. Candidate fixes for later, to be tested only with
fresh data: verify UNAFFECTED decisions on key controls, and let the verifier
accept a direct text link between ticket and control as a chain.

## Pre-registered: proposer chain requirement, A/B test (2026-10-15)

Registered before the change is run on any case.

- **Change (version B):** a proposer AFFECTED finding must carry an
  `evidence_path` that starts at a changed entity and ends at the control;
  findings without one are rejected with a message and can be resubmitted.
  The instructions say AFFECTED needs the control to govern the same rule,
  system, interface or process the change reaches, and that impact crossing
  into another functional area without an explicit link is UNCERTAIN.
  Verifier unchanged. Includes the null counter-evidence fix (`d6ca2e4`).
- **Baseline (version A):** frozen commit `799189a`, results in `suite-10`.
- **Test:** the same eight cases (CHG-004, CHG-002, CHG-041, CHG-026,
  CHG-029, CHG-016, CHG-049, CHG-010), one run, same settings, output
  `suite-12`. Version A is rescored with the current scorer (no model calls)
  so both have the same measures.
- **Adopt B for the held-out run only if both hold:** avoidable review items
  fall by at least 30%, and key controls recovered fall by no more than 3 of
  the 49 key misses. Otherwise version A goes to the held-out run.
- **Caveats stated in advance:** one run per version, and repeat runs of the
  same version already differ (precision 100% vs 78% on three cases); the fix
  was motivated by CHG-025, a tuned case; all eight cases have been seen once.

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
