# Architecture

## 1. Benchmark

The benchmark models one fictional bank's outbound cross-border payment flow:
instruction, validation, sanctions screening, fraud and limits, authorization,
transformation, dispatch, exceptions and repair, reconciliation, and reporting.

**Hidden graph** (`data/ground_truth/payment_graph_benchmark.json`, generated
from the hand-written seed `payment_graph_v0_1.json` by
`scripts/generate_benchmark.py`, seed `20261007`):

| Node type | Count | | Control criticality | Count |
|---|---|---|---|---|
| CONTROL | 101 | | KEY | 30 |
| DATA_ELEMENT | 12 | | STANDARD | 60 |
| PROCESS | 10 | | SUPPORTING | 11 |
| SYSTEM | 8 | | | |
| INTERFACE | 5 | | | |
| RULE, REPORT, EVIDENCE | 4 each | | | |

238 edges use the relationships USES, PRODUCES, FEEDS, TRANSFORMS, VALIDATES,
SCREENS, GOVERNED_BY, DEPENDS_ON, EVIDENCES (which propagate impact) and
COMPENSATED_BY (which does not). Generated controls come in families that share
a title prefix, for example "Required-field validation — daily completeness";
each has two semantically related dependencies so no single edge removal hides
a whole family.

**Changes** (`benchmark_changes.json`): 54 scenarios, 36 development and 18 test,
fixed at generation time. Types: field mapping (12), report (12), interface
(12), system (6), screening field set, message mapping, validation rule and
parameter (3 each).

**Labels** (`scripts/ground_truth.py`): a control is affected when the changed
entity reaches it through a propagating path in the hidden graph. No model
creates or edits labels.

## 2. Observable cases

`scripts/generate_observable.py` builds what a system may see for each change:

- `change_ticket`: title, text, changed entity IDs, implementation date.
- `visible_metadata`: graph nodes and a **degraded** copy of the edges.
- `control_documents`: one short procedure text per control, also degraded
  (legacy aliases, omitted sentences, occasional misleading "no impact" text).

Degradation removes 30% of links in two modes. *Random* removes edges uniformly.
*Change-correlated* removes edges nearest the changed entity first, while
keeping roughly (100 − level)% of the changed node's own edges, so the change is
never fully isolated. The primary condition is **30% change-correlated**.

Each generated case also carries `split` and a `degradation_manifest`. These
are evaluation-only. `scripts/case_io.observable_payload()` strips them, and
every runner passes only that payload to the agent.

## 3. Rules baseline

`scripts/baseline.py` starts from the changed entity IDs, follows visible
propagating edges (up to 6 hops), stops at controls, and ranks them by distance,
key status and ID. It uses no text, embeddings or model. At 30% correlated
degradation it finds 51 of 276 affected key-control pairs on the development
split (225 missed) and 18 of 162 on the test split (144 missed).

## 4. Detective agent

`scripts/detective.py`, function `investigate(case, llm, max_steps, persist, resume)`.

### Loop

Each step the model receives the instructions, the case context (ticket,
changed entities with descriptions, a non-control node index, the control
catalog with titles and criticality), a **notebook** of what it has learned so
far, a compact history and the remaining step count. It replies with one JSON
action:

| Action | Purpose |
|---|---|
| `trace_metadata {}` | Run the rules baseline on visible edges |
| `explore_node {node_id}` | A node's name, description and visible in/out edges |
| `search_controls {query, limit}` | Rank control documents by word overlap (never excludes any) |
| `inspect_control {control_ids:[≤15]}` | Full control text and edges; required before a finding |
| `submit_findings {findings:[≤8]}` | Decisions with evidence (below) |
| `finish {}` | Stop |

A finding is `{control_id, decision: AFFECTED|UNAFFECTED|UNCERTAIN,
ticket_quote, control_quote, causal_reason, counter_evidence, evidence_path}`.
Quotes must be exact substrings of the ticket and of that control's text; the
control must have been inspected; `evidence_path` may only name known nodes.
An AFFECTED finding from the agent must also carry an `evidence_path` that
starts at a changed entity and ends at the control (added 2026-10-15 to curb
cross-area over-claiming; see the A/B test in [results.md](results.md)).
Invalid findings are rejected with the reason, and valid ones in the same batch
are kept.

The instructions tell the agent that visible lineage is incomplete near the
change, so a missing edge is not counter-evidence; AFFECTED needs a functional
chain (the changed entity feeds a rule, system or process whose function the
control governs, for example because the control's family members are
governed by it).

### Robustness measures

These were added after live failures and are covered by tests:

- **Reply parsing.** gpt-oss returns `[reasoning, text]` content blocks; only
  the answer text is used. If the answer is empty, the adapter retries with a
  nudge at temperature 0.3, and as a last resort takes the last command-like
  JSON object from the reasoning text. The system message sets `Reasoning: low`.
- **Command spelling.** `{"tool", "arguments"}`, nested `function` calls and
  JSON-string arguments are accepted as `{action, args}`.
- **Truncation.** Batches are capped and fields kept short; complete findings
  are recovered from a reply cut off at the output limit.
- **Bounded prompts.** Inspected control text and explored nodes live in the
  notebook; only the two most recent tool outputs are kept in full.
- **Early finish.** Up to 3 reminders while controls are undecided and more
  than 3 steps remain.
- **Resume.** A saved state for the same case (checked by digest) restores the
  trace, findings, notebook and completed verifications, and continues.

### Verification

After investigation, every finding other than UNAFFECTED gets one verifier
call. The verifier sees the ticket, the changed entities, the two-hop
downstream neighbourhood with descriptions, the control and its edges, the
control's family members and their edges, the proposer's evidence path and the
hypothesis. It returns its own decision with quotes, which are validated the
same way. If the verifier's output is invalid, it gets one retry with the error.

- Proposer and verifier agree → that decision.
- They disagree, or verification fails → **UNCERTAIN** (human review).
- Proposer UNAFFECTED → recorded without a verifier call; it adds no
  recommendation and no review item.

### Variants

`--variant` selects the agent version: **A** (default; frozen check and
held-out run), **B** (AFFECTED needs a cited chain; rejected by its A/B rule)
and **C** (A plus three post-investigation steps, under test):

- **Coverage sweep:** controls still undecided are decided in batches of 6,
  key controls first, from the ticket, the change neighbourhood, the control
  text and family; these become ordinary findings and are verified.
- **Key re-check:** key controls marked UNAFFECTED also get a verifier call.
- **Tie-break:** on proposer/verifier disagreement a third call sees both
  arguments and the evidence and decides; only its UNCERTAIN, or a failed
  call, goes to human review.

`scripts/ensemble.py` combines several runs by majority vote (recommend at
2 of 3, review at 2 of 3 flagged) and ranks the review queue.

### Output

`recommended_control_ids` = rules baseline ∪ verified AFFECTED.
`uncertain_control_ids` = review queue. `uninvestigated_control_ids` = controls
with no decision (never treated as safe). The full trace, raw model replies and
coverage counts are saved after every step.

## 5. Running and scoring

| Script | Role |
|---|---|
| `run_detective_suite.py` | Run development cases, compute labels offline, score each case, aggregate; `--resume`, `--runs` for consistency |
| `detective_job.py` / `job_entry.py` | Submit the suite as a one-time serverless Databricks job; check status and output |
| `run_detective.py` | Single case from an exported file; `--replay` re-runs a saved transcript and fails if any prompt differs |
| `score_detective.py` | Score one saved result against supplied labels |
| `inspect_detective_run.py` | Step errors, actions, verifier outcomes, example disagreements |
| `probe_model.py` | Send the first prompt N times and report usable replies |

## 6. Information boundary

- Ground truth (`data/ground_truth`, `ground_truth.py`, `evaluate_baseline.py`
  label functions) is imported only by evaluation code.
- The agent receives `observable_payload(case)` only. Tests check that hidden
  fields and labels never appear in any prompt.
- Tools are read-only. The agent never writes graph edges.
