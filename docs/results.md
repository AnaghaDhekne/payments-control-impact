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
| Additional review volume (including useful recoveries) | ≤ 25% | 406 additional items beyond 64 rules items (+634% item volume) | Original gate not met; not a measure of wasted effort |
| Consistency over 5 runs | ≥ 95% | 80% (8 of 10 key-control pairs; development cases, see below) | Not met |

**Version A review composition:** 262 correct new recommendations, 18 incorrect
new recommendations, and 126 UNCERTAIN items. Of the uncertain items, 69 are
affected and 57 unaffected according to the offline synthetic answer key.
Thus **331 of 406 additional items (81.5%) are genuinely affected** and warrant
consideration; **75 (18.5%, or 4.2 per change) are unaffected** review overhead.
There are 470 items including the baseline's 64. These are item counts, not
measured review time. The volume gate includes correct recoveries and must not
be interpreted as 406 wrong findings or 406 unnecessary reviews. Affected
UNCERTAIN items remain excluded from the recovery score.

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

## Pre-registered: final bounded round, variant D vs A (2026-10-18)

Registered and frozen at 12:15 CT (commit `6757e83`), before any run of variant D. Last
improvement round of the POC; nothing is tuned after this note.

**Diagnosis that motivated it** (existing A results, offline):

| Where A's missed key controls ended | Held-out (18 cases) | Fresh-damage A, 2 runs |
|---|---|---|
| Proposer AFFECTED, verifier UNCERTAIN (sent to review) | **30 of 31** | 38 of 93 |
| Proposer UNAFFECTED, never verified | 1 | 55 |
| Undecided | 0 | 0 |

- Cause 1: the verifier withholds approval mainly because no visible edge links
  the change to the control (116 of 124 held-out disagreements cite a missing
  edge), although missing edges are expected. But only 55% of those held-out
  disagreements are truly affected (89% fresh, 37% frozen check), so accepting
  them outright would add false flags. A judgement step that sees both
  arguments is the supported fix.
- Cause 2: key controls in another functional area marked UNAFFECTED (for
  example creditor town name vs sanctions screening). No simple bounded rule
  separates these: of 1,332 key UNAFFECTED decisions, 65 are wrong, and a
  family-based re-check would be mostly wrong on the frozen-check cases. Not
  fixed in this round; documented as next-stage work.
- Undecided key controls: none in any A run, so the planned bounded check of
  undecided key controls has nothing to act on and is not implemented.
- False flags (18 held-out): mostly chains into reporting and reconciliation
  families and the manual-fallback control C11; both proposer and verifier
  agreed, so no single targeted fix; documented.

**Candidate:** variant D = A plus one fix, the tie-break step (identical code
to version C's): on a proposer/verifier disagreement a third call sees both
arguments and the evidence and decides; only its UNCERTAIN, or a failed call,
goes to review. No sweep, no key re-check, no voting, same model and prompts.

**Validation set:** five development changes under fresh damage (30% random,
main seed), never run under this condition: CHG-029, CHG-043, CHG-044,
CHG-052, CHG-053 (16 key misses by the rules). Unchanged A and D, two runs
each, output `freshdev-A` and `freshdev-D`. This small set is kept separate
from A's 18-case held-out result, which stands as the headline.

Submitted 12:17 CT: D runs 1–2 `252150333904575`, `201545758938808` (second
workspace).
Submitted 12:19 CT: A runs 1–2 `137347372014836`, `1113596348362003` (first
workspace).

**Result (2026-10-19, all 5 cases finished in both runs of both versions):**

| Pooled over 2 runs | A (unchanged) | D (A + tie-break) | Rule | Status |
|---|---|---|---|---|
| Key misses recovered (of 32) | **20 (62.5%)** | 18 (56.3%) | D ≥ A | **Not met** |
| Avoidable (unaffected) review items | 30 | **16** | D ≤ A | Met |
| Undecided key controls | 0 | 0 | D ≤ A | Met (equal) |
| Repeatability (25 key pairs, run 1 vs 2) | 76% | 76% | D ≥ A | Met (equal) |
| New-control precision | 86.4% | 87.2% | | |
| UNCERTAIN | 63 | 55 | | |
| Model calls | 682 | 738 | | |

**Decision: D is not adopted; A stays** (rule 1 failed). Run-to-run noise is
larger than the difference: A recovered 12 then 8, D 7 then 11, as the caveat
anticipated. The tie-break resolved 86 disagreements: 3 to AFFECTED (all
correct), 34 to UNAFFECTED (26 correct, 8 wrongly dismissed affected controls),
49 left UNCERTAIN (41 affected). It is conservative: it removes noise (avoidable
items 30 to 16) but rarely promotes a finding, and sometimes dismisses a true
one. No further tuning; the POC closes with version A.

**Keep D only if all hold** (pooled over the two runs of each version):
1. key-miss recovery equal to or higher than A's;
2. unaffected review items (avoidable items) not higher than A's;
3. undecided key controls not higher than A's (A had none so far, so this
   cannot be "reduced"; equal is accepted);
4. repeatability not worse: share of affected key controls with the same
   recommend / not-recommend decision in both runs, D not below A.

Otherwise A stays. If runs do not finish (capacity limits), A stays and the
attempt is reported as incomplete. Caveat stated in advance: 16 key misses
and two runs per version is a small sample; differences of one or two
controls are within run-to-run noise.

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
- **Moved workspace** (2026-10-17 10:38 CT): the first Free Edition workspace hit
  its daily model limit with 12–14 of 18 cases done per main run. All results
  were copied (`results/detective_runs.tar.gz`) to a second workspace, where C
  runs 1–3 and A runs 1–2 resumed from their saved steps, same code and model:
  job run ids `573060831255233`, `1105397747202884`, `672466506468221` (C 1–3),
  `167770105481789`, `845418444026208` (A 1–2).
- **Stability runs** (2026-10-17 18:47 CT, second workspace): C runs 4–6
  resumed, job run ids `572616146806835`, `956239171330891`,
  `729808572922086`.
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

**Result, rules 2 and 3 (2026-10-17, all 18 cases; C runs 1–3 vs A runs 1–2):**

| | C, majority of runs 1–3 | A run 1 | A run 2 | A mean |
|---|---|---|---|---|
| Key misses recovered (of 93) | **49 (52.7%)** | 46 (49.5%) | 47 (50.5%) | 46.5 (50.0%) |
| New-control precision | 98.1% | 96.8% | 97.1% | |
| UNCERTAIN (sent to review) | 34 | 65 | 38 | 51.5 |
| Avoidable review items per case | **0.33** (6) | 0.78 (14) | 0.44 (8) | 0.61 |
| Review-queue true share | 95.6% | 91.2% | 94.3% | |
| Uninvestigated controls | 0 | 7 | 4 | |
| Model calls (all 18 cases) | 4,752 (3 runs) | 1,165 | 1,131 | |

- **Rule 2 (recovery ≥ 50% and no more than 5 points below A): met.** 52.7%,
  2.7 points above A's mean.
- **Rule 3 (avoidable items ≤ 3.0 per case and below A): met.** 0.33 vs 0.61.
- **Rule 1 (stability between two ensembles ≥ 95%): not yet measured**; needs
  C runs 4–6. Single runs of C agree with each other no more than single runs
  of A do (pairwise 90.5% vs 90.7%), as expected: the fixes do not steady a
  single run; only the vote can, and that is what rule 1 tests.
- **Reading.** The gains over A are real but modest on this condition: +2.5
  key controls recovered, about half the avoidable items, a third fewer
  UNCERTAIN, no undecided controls. Random damage gives both versions a light
  review load (A: 0.6 avoidable items per case, against 4.2 on the held-out
  run), so this test does not stress the review-volume weakness as hard as the
  held-out condition did. The cost is about four times A's model calls.
  Ranked queue: top half 90% affected vs bottom half 86%, so the ranking adds
  little.

**Result, rule 1 and decision (2026-10-18, runs 4–6 complete, 18 cases each):**

| | Vote of runs 1–3 | Vote of runs 4–6 |
|---|---|---|
| Key misses recovered (of 93) | 49 (52.7%) | 46 (49.5%) |
| New-control precision | 98.1% | 100% |
| Avoidable review items per case | 0.33 | 0.17 |
| UNCERTAIN | 34 | 40 |

- **Rule 1 (the two votes agree on ≥ 95% of affected key-control pairs): not
  met.** 153 of 162 pairs (94.4%); 154 were needed. Single runs agree
  pairwise on 90.8% and all six on 78.4%, so voting removed about 40% of the
  disagreements but not enough.
- **Decision, by the registered rule (all three must hold): version C is not
  adopted; version A stays.** Rules 2 and 3 were met (on the runs 1–3 vote, as
  registered). Recorded as measured; the target is not revisited.
- **Also noted:** the second vote recovered 49.5%, just under 50%, so recovery
  under this damage condition sits at the 50% line for both versions and both
  votes; the review-volume gains held in both votes (0.33 and 0.17 avoidable
  items per case against A's 0.61).
- **What it means:** the tie-break and majority vote fix the review-volume
  weakness and narrow, but do not close, the consistency gap, at about four
  times A's model cost. Any further step (for example a five-run vote) is a
  new test, to be registered and run on cases not used here.

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
