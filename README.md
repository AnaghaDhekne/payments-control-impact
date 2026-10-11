# Payments Control Impact

Consulting-oriented POC for **control-impact assurance during outbound cross-border payments modernization**.

## Business question
When a payments system, rule, interface, report, or data flow changes, can a governed hybrid workflow identify affected key controls when dependency metadata is incomplete or stale—without unacceptable reviewer workload?

The POC does not assume GenAI is the answer. It compares a deterministic metadata/graph baseline with a hybrid approach and pre-registers conditions under which the GenAI layer should be rejected.

## Scope
One fictional bank's outbound cross-border payment flow: initiation/validation, sanctions screening, fraud/limit checks, authorization, message transformation, dispatch, exceptions, reconciliation, reporting, and relevant technology controls.

Planned benchmark:
- 80–150 controls and 50–60 change scenarios
- held-out evaluation set
- 0%, 30%, 60% metadata degradation
- random and change-correlated degradation
- narrative degradation in parallel with metadata

## Outcomes
Controls can receive multiple actions: `REASSESS_DESIGN`, `REFRESH_EVIDENCE`, `OUT_OF_CYCLE_TEST`. The workflow may also flag `CONTROL_GAP_REVIEW` or `UNCERTAIN`. Primary evaluation is affected vs. unaffected; action selection is secondary.

## Comparison
**Rules baseline:** explicit metadata/dependency traversal ranked by graph distance.

**Hybrid:** deterministic candidates + semantic retrieval over imperfect narratives + structured LLM control-level assessment.

At 0% degradation, recall parity is expected because the hybrid contains the deterministic step; the useful question is whether semantic expansion adds false positives/workload.

## Pre-registered decision criteria
At 30% **change-correlated** degradation, proceed only if the hybrid:
1. recovers at least 50% of key-control misses made by rules;
2. uses no more than 25% additional reviewer workload versus rules at the same degradation level; and
3. achieves at least 95% affected/unaffected agreement for key controls across five repeated runs.

`reviewer_workload = recommended_controls + uncertain_controls`.

## Benchmark integrity
Ground truth is created before narratives: design hidden dependency graph → derive affected controls in code → assign actions using frozen rules → generate imperfect documents → create degraded views. The evaluated workflow never receives the complete hidden graph.

Synthetic data can show the mechanism works under controlled conditions; it cannot establish client value. A successful POC justifies a shadow-mode pilot.

## Current status and Phase 2

The original configuration failed three held-out gates; see [final findings](docs/findings_and_gate_review.md). We are continuing with **evidence-backed dependency proposals, human approval, and deterministic impact reruns**. The new workflow and offline fixture are implemented; live model performance has not yet been evaluated. The fixture is not a successful AI benchmark.

Start with the [Phase 2 workflow and evaluation guide](docs/dependency_review_phase2.md).
