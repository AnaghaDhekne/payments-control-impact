# POC completion TODO — ordered execution plan

Status: OPEN. Owner: project maintainer. Updated: 2026-10-13.
Scope: Payments Control Impact, Phase 1 + Phase 2, synthetic benchmark. This is an execution checklist, not evidence that a gate passed. Check boxes only after saving reproducible artifacts. **Do not change the model, prompt, retrieval, thresholds, dataset, or scoring definitions after freezing and before held-out evaluation.**

## 0. Preserve the current state (before any further experiments)
- [ ] Record branch, commit SHA (starting reference: `68b78ed`), UTC date, Python version, dependency lock/version list, Databricks model endpoint/version, generation settings, seeds, and relevant environment limits in `docs/evaluation_manifest.md`.
- [ ] Save a read-only snapshot of the development outputs, raw per-run proposals, retrieval candidate sets, validation/rejection logs, review decisions, graph outputs, score files, and exact commands/configuration. Add hashes and paths to the manifest; do not commit secrets, tokens, private data, or oversized artifacts.
- [ ] Verify the reported 53.3% key-miss recovery and 82.2% control-level precision can be recomputed from raw 36-case development outputs. Record numerators, denominators, per-case counts, and aggregation method. Explicitly distinguish proposed edges, correct edges, newly surfaced controls, and key controls.
- [ ] Record the complete final pipeline: GPT OSS 120B (confirm exact endpoint), two-stage prompting, k=30 and k=50 retrieval merge, 5-run vote rule, rule-based validation, graph-impact `key_only`, Jaccard thresholds (including v3 conditional), human/oracle review, and impact rerun. Explain the rationale and which settings were selected using development labels.
- [ ] Identify and document any development-data tuning or repeated test-set peeking. If the held-out set has already informed tuning, designate a genuinely untouched new test set before claiming independent validation.
**Done when:** an independent reviewer can reconstruct exactly what was evaluated without accessing hidden labels from runtime.

## 1. Audit correctness and information boundaries
- [ ] Trace the execution path in `scripts/dependency_proposals.py`, retrieval, baseline, review, and scoring modules; confirm which code actually produced the latest numbers (not just which code exists).
- [ ] Check that prompts, retrieval, candidate selection, graph-impact filtering, Jaccard filtering, voting, and reviewer inputs never read ground-truth edges, degradation manifests, target labels, or offline score outputs. Add a negative leakage test.
- [ ] Verify `key_only` uses *observable* control criticality, not hidden impact labels. Confirm no hidden oracle is used to decide which candidates are presented.
- [ ] Check quote matching, IDs, edge direction, relationship types, duplicate handling, existing-edge exclusion, invalid JSON, abstentions, empty retrieval, and stale-batch/version binding; test failure paths.
- [ ] Confirm that Jaccard thresholds are computed from permitted visible inputs, are applied in the stated direction, and do not accidentally remove true zero-overlap dependencies except through the documented vote exception.
- [ ] Recheck the C06 zero-lexical-overlap cases: verify k=50 inclusion, merged retrieval, edge correctness, and that the method is not hard-coded to C06 or specific change IDs.
- [ ] Validate graph reachability and transitive impact after approved edges; reject incorrect edge direction/types and never auto-approve proposals.
- [ ] Separate oracle adjudication (simulation) from human review (real workflow) in code, output filenames, and claims. Zero incorrect oracle-approved edges is not independent safety evidence.
- [ ] Add unit/integration tests for the above, including no-label access, threshold boundary values, repeated runs, and adversarial or ambiguous narratives.
**Done when:** observable-only operation and scoring isolation are tested, not just asserted.

## 2. Freeze a reproducible evaluation protocol
- [ ] Create `docs/heldout_protocol.md` before running test. Specify exact dataset/version/hash, split method, sample sizes, scenario families, random vs change-correlated degradation, 0/30/60% levels as applicable, and definition of key controls.
- [ ] Preserve the existing 54-scenario / 101-control benchmark provenance; document why 36 development cases and the remaining test cases are or are not sufficiently independent. Check for near-duplicate narratives or shared templates across splits.
- [ ] Predeclare the primary outcome: key misses recovered / baseline key misses, with exact handling for zero-denominator cases, per-case vs pooled averaging, and reviewer assumptions.
- [ ] Predeclare precision: true newly recommended controls / all newly recommended controls (or another clearly named metric); separately report edge precision, false-positive controls, false-positive edges, and total reviews. Do not silently switch between metrics.
- [ ] State all Phase 1 original gates (recovery >=50%, workload increase <=25%, agreement >=95%, parse failures=0) and Phase 2 provisional gates (recovery >=50%, precision >=80%, incorrect approved edges=0, reviews per recovered key <=3). Do not call 2/4 gates overall success. Note any formally revised gates as *revised*, not original.
- [ ] Define the 5-run stability calculation, voting threshold, repeated-call cost, latency, review workload, and exact treatment of UNCERTAIN and excluded controls.
- [ ] Define comparison baselines: metadata-only, original Phase 1, original Phase 2, 50–70% lineage repair, and improved Phase 2. Keep evaluation splits and scoring comparable; explain when they are not.
- [ ] Lock code SHA, model endpoint/version, prompts, retrieval settings, thresholds, metric definitions, and all random seeds in a config/manifest; no post-test tuning on the held-out set.
- [ ] Predefine pass/fail reporting and uncertainty (per-case confidence intervals or bootstrap; rule-of-three bound where zero misses are observed, with denominator). Small test samples cannot prove zero future misses.
**Done when:** protocol is committed and frozen before the first independent test run.

## 3. Reproduce locally without Databricks
- [ ] Create a fresh Python 3.12 environment, install pinned requirements, and run `python -m pytest -q`; save the full output and failures.
- [ ] Run benchmark and observable-input generation using the documented commands; verify counts, hashes, seeds, and split isolation.
- [ ] Run baseline, graph repair comparator, offline scoring, and review demo using saved proposals; ensure all work without live model access.
- [ ] Confirm deterministic scoring on identical saved artifacts and verify results agree with the reported development metrics.
- [ ] Add or fix a one-command offline replay and document exact inputs/outputs; make the script fail loudly if artifacts are missing.
**Done when:** a new contributor can replay scoring without Databricks or secrets.

## 4. Run the frozen held-out evaluation (when Databricks is available)
- [ ] Confirm model serving access, quotas, permissions, endpoint identity, context/token limits, and projected cost. Never silently substitute a different model.
- [ ] Run the frozen pipeline on the untouched held-out cases, including all specified degradation strata, with the prescribed 5 independent calls per case. Save every raw response, parse failure, candidate list, vote, filtered proposal, citation, and review result.
- [ ] Perform oracle adjudication *only in the offline evaluation layer* to measure upper-bound proposal potential; separately run a blinded human-review sample if possible.
- [ ] Score baseline and improved model on exactly the same cases; compute pooled and per-case key-miss recovery, control precision, edge precision, false positives, reviews per recovered key, UNCERTAIN burden, excluded-sample misses, 5-run agreement, parse failures, latency, and cost.
- [ ] Compare against lineage repair using clearly specified repair rates and fair evaluation conditions. Include the original Phase 1 and Phase 2 configurations where feasible.
- [ ] Report every gate individually with PASS/FAIL/NOT TESTED; provide uncertainty intervals and breakdowns by degradation mechanism, level, key vs supporting controls, and scenario family.
- [ ] Investigate any failures **without modifying the frozen run**. If improvements are needed, label them as a new experiment and reserve a fresh untouched test set for a new confirmation.
**Done when:** immutable raw outputs, a reproducible scorer, and an unambiguous held-out gate table are committed or linked.

## 5. Validate practical safety and human workload
- [ ] Have reviewers assess proposed edges using only visible evidence; capture APPROVE / REJECT / UNCERTAIN, rationale, time per review, and disagreements. Do not treat oracle decisions as real reviewer accuracy.
- [ ] Sample excluded controls and rejected edges to measure silent misses; track especially high-criticality controls.
- [ ] Test cases with stale narratives, legacy names, no lexical overlap, conflicting evidence, unsupported relationship types, new entities, and ambiguous controls.
- [ ] Check approval audit trails, case-version integrity, replay behavior, rollback of mistaken edges, least privilege, and handling of sensitive data (synthetic-only in this repo).
- [ ] Establish a pilot stop rule, escalation path for uncertain controls, and explicit human sign-off. Zero observed misses is not a production guarantee.
**Done when:** reviewer burden and safety gaps are measured rather than inferred.

## 6. Reconcile documentation and claims
- [ ] Update `README.md` current status: development gates passed for improved Phase 2; held-out result pending until independently measured. Remove outdated 'live evaluation is next' and 'no performance success claim' wording.
- [ ] Rewrite `docs/executive_summary_phase1_phase2.md` so opening, bottom line, results tables, Phase 2 gates, limitations, and conclusion all describe the same version and distinguish old failures from the improved dev result.
- [ ] Correct model labels: initial Llama 4 Maverick vs later GPT OSS 120B, exact endpoints, experiments, and dates. Never attribute later results to the earlier model.
- [ ] Update `docs/phase2_results.md` and `docs/dependency_review_phase2.md` with clearly dated historical vs current results; preserve negative findings as history.
- [ ] Audit `docs/findings_and_gate_review.md`, `docs/executive_summary_final.md`, `docs/executive_review_pack.md`, `docs/stakeholder_brief.md`, `docs/runbook.md`, and `output/README.md` for stale or contradictory numbers.
- [ ] Explain why 53.3% recovery / 82.2% precision (dev) do not imply all four original or provisional gates pass. Explicitly show that lineage repair remains stronger on its reported comparison and note any split mismatch.
- [ ] Add a results provenance table mapping each claim to commit, config, dataset split, command, artifact path, scorer, and review mode.
- [ ] Document architecture, rationale, known limitations, failure modes, operating assumptions, and Databricks setup/teardown steps for a future maintainer.
**Done when:** a reader cannot confuse development success, held-out success, oracle simulation, or production readiness.

## 7. Maintainability, quality, and handoff
- [ ] Review repository tree for duplicated/obsolete scripts, accidental generated files, unused outputs, and temporary experiments. Archive with an index rather than deleting evidence needed to reproduce claims.
- [ ] Ensure scripts have module docstrings, clear functions/types, comments explaining non-obvious decisions, meaningful errors, and no hard-coded case-specific shortcuts.
- [ ] Pin runtime/development/LLM dependencies; add configuration examples and safe secret handling; check .gitignore and tracked files for credentials.
- [ ] Add tests for pipeline orchestration, graph impact, filters, voting, scoring, reviewer approvals, and regression fixtures for the breakthrough cases.
- [ ] Set up CI for tests, formatting/linting, and static checks that require no Databricks access.
- [ ] Update architecture diagram, runbook, contribution guide, artifact inventory, and troubleshooting for quota limits, endpoint errors, malformed JSON, and missing packages.
- [ ] Run a clean-clone setup and offline replay from the README; fix any command or path that fails.
**Done when:** another engineer can understand, run, audit, and extend the project independently.

## 8. Final presentation and decision
- [ ] Prepare a concise executive narrative: business problem -> missing lineage -> baseline -> AI proposal workflow -> measured result -> comparison -> safeguards -> decision.
- [ ] Create one results table separating dev and held-out splits, original and improved configurations, recovery, precision, workload, stability, parse failures, and review mode. No invented or mixed metrics.
- [ ] Demonstrate one correct recovered key control, one rejected incorrect edge, and one UNCERTAIN/excluded case with traceable evidence and a graph before/after.
- [ ] Present lineage repair as primary where feasible and AI as a supplementary evidence-backed discovery mechanism unless new independent results justify a stronger claim.
- [ ] Include reproducibility manifest, limitations, risks, cost/latency, reviewer requirements, and next pilot criteria. Mark any untested criterion clearly.
- [ ] Run a final evidence audit: every number in slides, docs, and demo matches a saved scored artifact.
- [ ] Decide outcome honestly: development proof, independently validated POC, pilot candidate, or further research. Do not label production-ready without operational validation.
**Done when:** the POC can be presented without overstating results and the audience can reproduce the key claims.

## Stop/go sequence
1. **Now, offline:** Sections 0–3. Do not use the held-out labels to tune.
2. **When Databricks returns:** Section 4, once, under the frozen protocol.
3. **After evaluation:** Sections 5–8. Update all claims to the actual held-out results.
4. **If gates fail:** Preserve the negative run, diagnose on development data, create a versioned revision, and obtain a new untouched holdout for confirmation.
