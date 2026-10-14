# Phase 2: evidence-backed dependency proposals

Status: held-out evaluation completed 2026-10-13. Both Phase 2 gates pass
on 18 test cases (recovery 57.6%, precision 91.2%). Results are
oracle-adjudicated; human review has not been conducted. See
docs/final_report.md for the current status.

## Workflow

An LLM proposes missing direct entity-to-control dependencies from observable
metadata, change tickets, and control documents. Each proposal cites exact text
from the ticket and control document. Mechanical validation rejects unknown IDs,
unsupported relationships, existing/duplicate edges, and fabricated quotations.
Quotation matching does not prove a dependency: a reviewer must check direction,
relationship, and whether the evidence establishes a DIRECT link.

Only an explicit APPROVE decision inserts an edge. REJECT, UNCERTAIN, and pending
proposals never change the graph. Rules rerun and show impact paths. Every review
requires reviewer, timestamp, and reason, and is bound to a case digest. Reviewer
names are user-entered audit fields, not authenticated identities. The workflow
is a local POC, not an enterprise authorization system.

Current scope: direct non-control entity-to-control edges. Missing upstream
entity-to-entity links are not repaired in this version. Strict abstention may
reduce recovery when narratives lack sufficient evidence. The prompt includes
all supplied control documents; assess input size before using a larger corpus.

## Offline example

```bash
python -m scripts.run_dependency_review demo --output output/dependency_review_demo.json
python -m pytest -q
```

The example is HAND-AUTHORED, with a SIMULATED reviewer. Baseline finds no controls;
the approved dependency makes the address control reachable. It verifies wiring,
not AI accuracy or benchmark success.

## Live development run

Export one development observable case into case.json, excluding the degradation
manifest and any hidden labels. Install requirements-llm.txt and authenticate
to the workspace as in docs/runbook.md. Then:

```bash
python -m scripts.run_dependency_review propose --case case.json --output proposals.json
```

To validate an already saved raw response instead of making a live call, add
`--response response.json`. Preserve the raw response and model configuration.

Review the proposals without consulting hidden labels. Write reviews.json as a
list of objects with proposal_id, decision (APPROVE/REJECT/UNCERTAIN), reviewer,
reviewed_at (ISO timestamp), and reason. Then:

```bash
python -m scripts.run_dependency_review review --case case.json --batch proposals.json --reviews reviews.json --output reviewed_result.json
python -m scripts.score_dependency_review --result reviewed_result.json --labels labels.json --output metrics.json
```

The scorer is OFFLINE ONLY. labels.json contains case-specific
affected_control_ids, key_control_ids, and correct_proposal_ids from independent
adjudication. Never expose it to the proposer or impact reviewer. Correctness of
new direct links must be adjudicated explicitly; affected control status alone
does not validate a claimed direct edge.

## Evaluation before any success claim

1. Begin on development cases, with evidence sufficient to test the mechanism.
2. Measure proposal precision, approved-edge correctness, key-miss recovery,
   excluded key misses, all proposal reviews (including rejections), pending and
   uncertain queues, final control reviews, reviewer minutes, and LLM cost.
3. Compare against rules AND a human reviewing the same documents without AI.
   Deterministic traversal after approval does not demonstrate repeatable LLM
   proposals; assess proposal variation across five independent runs separately.
4. Proposed gates for stakeholder agreement BEFORE freezing: >=50% key-miss
   recovery, >=80% reviewed proposal precision, zero incorrect approved edges,
   and <=3 proposal reviews per recovered key control. These are provisional
   phase-2 targets, not replacements for the original pre-registered gates.
   Report absolute final control-review workload and measured reviewer time too.
5. Use fresh, untouched scenario families for final testing. Existing test cases
   have already influenced design; merely holding out another release of the
   same scenario is insufficient. Freeze documents, labels, model, prompt,
   review rubric, and thresholds before that evaluation.

The simulated repair comparator restores known edges from the hidden graph.
It estimates the benefit of correct repair, not discoverability or repair cost.
Do not compare it to this workflow as though it were a deployed repair method.

## Development evaluation results (2026-10-11)

Model: databricks-llama-4-maverick, temperature=0, max_tokens=6000.
36 development cases, 30% correlated degradation, oracle-adjudicated reviews.

| Gate | Threshold | Result | Status |
| --- | --- | --- | --- |
| Key-miss recovery | >= 50% | 3.6% | FAIL |
| Reviewed proposal precision | >= 80% | 21.3% | FAIL |
| Zero incorrect approved edges | 0 | 0 | PASS |
| Reviews per recovered key | <= 3 | 9.4 | FAIL |

5-run proposal agreement: 20.6%. The model is highly non-deterministic even at
temperature 0. Only 5 of 36 cases produced any correct proposals. Full results
in docs/phase2_results.md.

Key failure modes: prompt biases toward DEPENDS_ON (misses GOVERNED_BY and
EVIDENCES edges), model abstains too aggressively (~2 proposals/case when
~7 needed), low precision (21.3%), and high non-determinism (20.6% agreement).

