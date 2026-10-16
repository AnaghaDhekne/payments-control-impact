# Results

## Final: held-out test run (2026-10-16)

Pre-registered below ("Pre-registered: held-out test run"). Job
`862812162377923`, variant A (chosen by the A/B rule), agent code `d149a52`
(later commits changed only docs and the app), all 18 test-split cases, one
run, 30% change-correlated degradation, `databricks-gpt-oss-120b`. All 18 cases
finished; 8 controls uninvestigated; 1,280 model calls.

| Case | Change (template, release) | Key misses | Recovered | New true / false | Uncertain |
|---|---|---|---|---|---|
| CHG-003 | Creditor town-name mapping, 1 | 19 | 18 | 37 / 6 | 11 |
| CHG-021 | Creditor town-name mapping, 2 | 19 | 15 | 39 / 1 | 8 |
| CHG-039 | Creditor town-name mapping, 3 | 19 | 15 | 34 / 3 | 11 |
| CHG-009 | Screening interface, 1 | 10 | 10 | 20 / 0 | 0 |
| CHG-027 | Screening interface, 2 | 10 | 10 | 20 / 0 | 0 |
| CHG-045 | Screening interface, 3 | 10 | 10 | 20 / 0 | 0 |
| CHG-006 | Screening field-set, 1 | 7 | 4 | 8 / 1 | 5 |
| CHG-024 | Screening field-set, 2 | 8 | 5 | 7 / 1 | 12 |
| CHG-042 | Screening field-set, 3 | 7 | 6 | 9 / 1 | 8 |
| CHG-015 | Screening engine, 1 | 7 | 2 | 3 / 0 | 10 |
| CHG-033 | Screening engine, 2 | 7 | 1 | 3 / 0 | 11 |
| CHG-051 | Screening engine, 3 | 6 | 2 | 3 / 1 | 9 |
| CHG-018 | Ledger-posting feed, 1 | 5 | 5 | 14 / 0 | 11 |
| CHG-036 | Ledger-posting feed, 2 | 5 | 5 | 19 / 4 | 8 |
| CHG-054 | Ledger-posting feed, 3 | 5 | 5 | 18 / 0 | 11 |
| CHG-012 | Payment reject report, 1 | 0 | – | 3 / 0 | 1 |
| CHG-030 | Payment reject report, 2 | 0 | – | 3 / 0 | 9 |
| CHG-048 | Payment reject report, 3 | 0 | – | 2 / 0 | 1 |
| **Total** | | **144** | **113 (78.5%)** | **262 / 18 (93.6%)** | **126** |

| Gate | Target | Held-out | Status |
|---|---|---|---|
| Key-miss recovery | ≥ 50% | 78.5% (113 of 144; Wilson 95% interval 71.1–84.4%) | **Met** |
| Added reviewer workload | ≤ 25% | 406 items beyond the baseline vs 64 rules items (+634%) | Not met |
| Consistency over 5 runs | ≥ 95% | 80% (8 of 10 key-control pairs; development cases, see below) | Not met |

Review burden (descriptive): 75 avoidable items, 4.2 per case; 81.5% of items
beyond the baseline are genuinely affected.

**Reading.** The stop rule (held-out recovery below 50%) is not triggered.
Held-out recovery is higher than the frozen development check (65.3%, interval
51.3–77.1%); the intervals overlap, so this is not evidence the method got
better, only that it was not overfitted to the development cases. Performance
depends strongly on the change type: screening interface and ledger-posting
feed changes 45 of 45, town-name mapping 48 of 57, screening field-set 15 of
22, **screening engine 5 of 20**. Screening-engine changes are the clear weak
spot and the first thing a practitioner review should look at. Payment reject
report changes had no key misses and produced no false flags.

**Caveats.** One run (repeat runs vary, see consistency); synthetic benchmark
whose controls come in families; the test cases were examined during the
Phase 2 diagnosis, though never by this agent; gate 2 is unreachable on this
benchmark by any method that passes gate 1 (see [evaluation.md](evaluation.md)).

## Consistency: 3 cases × 5 runs (job 189647926488694, 2026-10-15)

| Run | Key recovered | New-control precision | Uncertain | Avoidable items |
|---|---|---|---|---|
| 1 | 7 of 8 | 78.1% | 27 | 20 |
| 2 | 7 of 8 | 90.5% | 11 | 8 |
| 3 | 8 of 8 | 90.0% | 35 | 22 |
| 4 | 8 of 8 | 88.9% | 48 | 39 |
| 5 | 8 of 8 | 96.0% | 40 | 28 |

Agreement: 8 of 10 affected key-control pairs got the same recommend /
not-recommend decision in all five runs (80%, target 95%): **not met**.
Recovery is stable (87.5–100%); the volume of UNCERTAIN items is not (CHG-025:
6 to 36). Cases CHG-014, CHG-025, CHG-017 (development, tuned).

## Pre-registered: version C with majority vote, fresh-damage test (2026-10-16)

Registered before any run of version C. Purpose: fix the two gaps the
held-out run left (stability 80% vs 95%; about 4 avoidable review items per
change).

- **Version C** (`--variant C`) = version A's instructions plus three steps
  after the investigation: (1) a coverage sweep that asks for a decision on
  every control still undecided, in batches of 6, key controls first; (2) key
  controls the agent marked UNAFFECTED are sent to the verifier too; (3) when
  proposer and verifier disagree, a tie-break call sees both arguments and
  the evidence and decides; only its UNCERTAIN (or a failed call) goes to a
  person. Model replies that use the tool name as the JSON key are now
  understood. Empty-answer retries: the first retry keeps temperature 0
  (nudged prompt), only a second adds 0.3 (applies to A and C alike).
- **Majority vote** (`scripts/ensemble.py`): three runs per case; recommend
  when the rules reach a control or at least 2 of 3 runs recommend it; review
  when at least 2 of 3 runs recommend it or send it to review; review items
  ranked by how many runs flagged them.
- **Cases:** the 18 test-split changes with **freshly damaged lineage**: 30%
  random degradation (`--level 30 --mode random`), main seed. Removed edges
  overlap the held-out run's damage by 30%, i.e. at chance; 93 key misses
  (held-out: 144). A new seed under the main condition was checked and
  rejected: 91% of removed edges were the same. The changes, tickets and
  controls are those of the held-out run.
- **Submitted** 2026-10-16 09:27 CT at commit `f210902`. Job run ids: C runs
  1–6 `1032044827556125`, `59522537221119`, `565845798253507`,
  `987848725205628`, `1121319492587016`, `1018519589285706`; A runs 1–2
  `1034822050524777`, `77895592225147`.
- **Order changed, scope unchanged** (2026-10-16 12:45 CT, before any result
  was scored): the endpoint's capacity is shared, so C runs 4 and 5 were
  stopped after 3 and 2 cases, and C run 6 just after it started, to let both
  A runs start; all three resume later
  (`--resume`, same folders). No run, case or rule is dropped.
- **Runs (parallel jobs):** version C, runs 1–6 in `fresh-C` (ensembles
  {1,2,3} and {4,5,6}); version A, runs 1–2 in `fresh-A` as the comparison on
  the same cases.
- **Adopt C with majority vote for the practitioner-review stage only if all
  hold** (ensemble = runs 1–3; A = mean of its two runs):
  1. **Stability:** the two ensembles give the same recommend / not-recommend
     decision on ≥ 95% of affected key-control pairs.
  2. **Recovery:** ensemble key-miss recovery ≥ 50% and no more than 5 points
     below A's.
  3. **Review volume:** ensemble avoidable review items ≤ 3.0 per case and
     below A's.
  Otherwise version A stays, and the result is reported as it is.
- **Also reported, not gated:** single-run pairwise agreement for C and for
  A; the affected share in the top vs bottom half of the ranked review
  queue; model calls per case; every case.
- **Caveats stated in advance:** the fixes are tested together, so a gain
  cannot be assigned to one of them; the test changes were run once before
  (held-out), and three screening-engine results (CHG-015, 033, 051) were
  inspected on 2026-10-16 after the fixes were designed: in all three every
  control was decided and the misses were key controls the agent marked
  AFFECTED and the verifier left UNCERTAIN (no visible edge), which is what
  the tie-break addresses; no screening-specific change was made; random
  damage is a different condition from the main one, so these numbers are
  not comparable with the held-out 78.5%.

## Tuned development cases (2026-10-14/15)

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
| Consistency over 5 runs | ≥ 95% | 80% (see Consistency above) | Not met |

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

**Outcome (job 663596150833963, `suite-12`, completed 2026-10-15).**

| | A (`suite-10`) | B (`suite-12`) |
|---|---|---|
| Key misses recovered | 32 of 49 (65.3%) | 27 of 49 (55.1%) |
| New true / false | 79 / 8 (90.8%) | 50 / 0 (100%) |
| Uncertain | 82 | 86 |
| Avoidable review items | 56 | 46 (−18%) |
| Uninvestigated | 2 | 42 |
| Cases ending at the step budget | 0 | 4 of 8 |

Neither condition holds (avoidable items fell 18%, not 30%; recovery fell by
5, not ≤ 3). **Version A goes to the held-out run.** B removed every wrong flag
but turned them, and some true findings, into UNCERTAIN items, and spent its
budget on resubmissions: half its cases hit the step limit, leaving 42 controls
undecided. A cited-chain requirement trades recall and coverage for precision.

## Pre-registered: held-out test run (2026-10-15)

**Submitted** 2026-10-15 with `--variant A`, job run id `862812162377923`,
output `heldout-final`.

Registered before the A/B result is known and before any test case is run.

- **Cases:** all 18 test-split changes (CHG-003, 006, 009, 012, 015, 018, 021,
  024, 027, 030, 033, 036, 039, 042, 045, 048, 051, 054), 30% change-correlated
  degradation, one run.
- **Agent:** the variant selected by the A/B rule above (`--variant A` or `B`),
  at the commit that records this note; both variants' instructions are
  byte-identical to the measured commits `799189a` (A) and `67bd813` (B).
- **Command:** `detective_job submit --split test --confirm-heldout
  final-frozen-run --variant <A|B> --output-dir
  /Volumes/workspace/default/detective_runs/heldout-final`.
- **Rules:** no code, prompt or model change after submission; an interrupted
  run may only be resumed with the same variant (enforced); every case is
  reported; all three gates and the review-burden measures are reported
  whatever they show.
- **Caveat stated in advance:** the test cases were examined during the earlier
  Phase 2 diagnosis (not by the detective), so this is the best available
  unseen evaluation, not a pristine one.

## Next steps

Done: diagnosis of UNCERTAIN, gate-2 decision, consistency, frozen check, A/B
test, held-out run.

1. Practitioner review of a sample of AFFECTED and UNCERTAIN findings from the
   held-out run, starting with the screening-engine cases (5 of 20 recovered).
2. Stability: majority vote over three runs per case; re-measure agreement.
3. Review volume: verifier treatment of direct text evidence (CHG-026) and a
   second look at UNAFFECTED key controls (CHG-029), tested on fresh cases only.
4. A pilot decision on a small real change set with control owners.

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
