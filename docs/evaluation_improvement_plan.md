# Evaluation improvement plan — development first

Date: 2026-10-08  
Project: Payments Control Impact  
Status: proposed experiments; **not measured improvements**

## Objective and decision rule

Improve the existing graph + LLM approach toward the **pre-registered** gate at **30% change-correlated degradation**: recover at least **50% of the key controls missed by the graph-only baseline**, increase **reviewer workload by no more than 25%** (count AFFECTED **and** UNCERTAIN), and obtain **at least 95% identical key-control decisions across five repeated runs**. Report remaining key-control misses, including those omitted entirely from recommendations. These are POC thresholds, **not a pilot authorization**. A pilot requires zero observed key-control misses in the surfaced AFFECTED + UNCERTAIN set, a sampled review of excluded controls, sample size, and an uncertainty bound (rule of three: about 3/n when zero misses are observed).

**Do not adjust thresholds, labels, ground truth, the held-out split, or reported results to make the model pass.** Optimize on development data, lock the procedure, and then run the held-out test once as a confirmation. If it fails, report failure and recommend lineage improvement as appropriate.

## What is actually observed

Source: `output/result_summary_and_actions.txt`, generated 2026-10-07; model `databricks-llama-4-maverick`, temperature 0, `top_k=20`. The hybrid was evaluated on **five** test scenarios and **three** repeated runs, whereas the baseline JSON contains **18** test scenarios. Its 30%-correlated condition has **68 affected key-control pairs** across those five scenarios: baseline recall **10.3%**, hybrid recall **71.6%**, recovered misses **68.3%**, workload **+442.2%**, agreement **94.7%**, zero parsing failures. These are preliminary and **do not pass** the agreed workload gate; stability is not yet a valid five-run result. The existing report's alternate gates (40% recovery, <100% workload, 100% agreement) are **not** the approved criteria.

At 30% random degradation, the report shows 43.2% recovery and +90.4% workload; at 60% correlated, 77.9% recovery and +970.8% workload. The apparent recovery/workload tradeoff is the research question, not evidence of readiness.

## First fix: correctness and accounting

1. Inspect `scripts/hybrid.py`: `hybrid_rank_controls()` currently unions **every** parsed LLM control ID with baseline IDs, even when the decision is `UNAFFECTED`. This is a classification/aggregation bug, not a tuning opportunity. Preserve raw predictions, but never silently treat `UNAFFECTED` as a positive recommendation.
2. Keep separate output classes: `AFFECTED` (with action), `UNAFFECTED`, `UNCERTAIN`, and `POSSIBLE_CONTROL_GAP` (flag for human review; do not invent control IDs). Baseline IDs remain included. Affected and uncertain are **both** surfaced and count toward workload; possible gaps also need an explicitly accounted review queue.
3. Add per-change, per-control audit rows: change_id, control_id, baseline_flag, retrieved_flag, raw_decision, confidence, action, final_class, surfaced_for_review, evidence/reason, ground_truth_key_affected (evaluation only), run_id, degradation mode/level, split, model identifier, prompt version.
4. Recompute the metrics from those rows, not from a prose report. Measure false positives, uncertain rate, excluded key misses, and retrieval coverage. Validate that the ground truth never enters prompts or candidate retrieval.
5. The summary's `output/baseline_results.json` is 18-case while hybrid files are five-case. Match **the exact same case IDs** before comparing baseline/hybrid recall or workload. At 0% degradation, recovery is **N/A**, not a pass due to a 0/0 placeholder.

## Development experiments (one change at a time)

Use **development** split only. Save the untouched current outputs as baseline artifacts. Maintain a run ledger with experiment ID, git commit, seed, model, prompt, top_k, split, threshold/cap, cost, and full metrics.

A. **Correct union semantics**: remove `UNAFFECTED` from positive outputs, preserve `UNCERTAIN` as a review category. Evaluate recovery, missed key controls, and workload. This should be the first ablation.

B. **Improve candidate retrieval before tightening filters**: compare current token Jaccard to field-aware matching (changed payment field, address structure, system, process, control family) and optionally graph-neighborhood candidate expansion. Use only observable degraded metadata and narratives; measure candidate-set recall of truly affected key controls and false candidate count. Consider top_k 20 vs 30 vs 40 and document the latency/workload tradeoff. No access to hidden graph.

C. **Evidence-grounded classification**: require the model to cite a change-ticket fragment and a control-document fragment for each AFFECTED or UNCERTAIN claim. If evidence is insufficient, output UNCERTAIN; do not fabricate links. Try a two-stage process: broad candidate discovery, then per-candidate evidence verification. Compare against the corrected single-stage model.

D. **Ranking, not silent exclusion**: rank LLM-only AFFECTED by confidence plus evidence quality; keep UNCERTAIN visible in a separate, counted queue. Evaluate multiple reviewer-budget operating points and show a **recall–workload frontier**. Do not cap or filter solely to meet the workload target if key misses rise. Confidence >=0.8 and top-10 caps are hypotheses to test, not guaranteed fixes. A 25% increase over a tiny baseline workload may allow very few extra candidates: report the absolute counts as well.

E. **Stability**: keep model, input ordering, prompts, decoding, endpoint configuration and seed fixed where supported; run five repeats. Compute the fraction of key-control **decisions** identical across all five, not “4 of 5 runs”. Consensus/intersection must not be claimed to guarantee safe or perfect reproducibility: it can increase missed controls. Measure the tradeoff.

F. **Lineage repair comparator**: add a metadata repair scenario with comparable effort assumptions; determine whether repairing observable lineage recovers as much key-control recall with lower workload. If the apparent AI gain is primarily information better lineage would supply, recommend fixing lineage instead.

## Final evaluation matrix

Run identical held-out cases for both methods: 0% random (correlated is equivalent at zero), 30% random, **30% change-correlated (primary)**, 60% random, and 60% change-correlated. Degrade narrative documents according to the benchmark's defined rules as well as graph links. Do **five** repeated model runs per condition after the procedure is locked. Preserve both per-case and aggregate outputs.

Report for each condition: number of cases, number of affected key-control pairs, baseline hits/misses, hybrid hits/misses, recovered misses and recovery fraction, affected recall, affected+uncertain review counts, workload increase percentage and absolute change, false positives, uncertainty queue size, excluded-list sampled misses, exact five-run key-decision agreement, parse failures, model calls/latency, and lineage-repair comparator. Never substitute illustrative infographic figures for measured results.

## Go / no-go

**POC value gate, primary condition only:** recovery >=50%; incremental reviewer workload <=25%; exact five-run key-control decision agreement >=95%; report parsing failures and residual key misses. A failed gate is a **no-go under current design**, not permission to loosen thresholds.

**POC stop/redirect:** if recovery <50% at 30% correlated, or no safe operating point meets workload/stability, stop claiming POC success. If comparable lineage repair supplies most of the gain, recommend lineage repair rather than AI.

**Pilot safety gate (separate):** zero observed missed key controls in AFFECTED+UNCERTAIN outputs on the defined validation sample; review a sample of excluded items for hidden misses; report n and the approximate 95% rule-of-three upper bound 3/n for zero observed misses. A five-case benchmark cannot establish a credible pilot safety claim. Human review of only surfaced items cannot find omissions.

## Databricks execution and Genie

**Databricks notebooks / Python** should execute the existing scripts, run model serving calls, and write evaluation records. **Genie** is a natural-language analytics interface over governed tables; use it to **inspect and summarize persisted run data**, not as a replacement for notebook execution, model calls, code editing, or ground-truth validation.

1. Sync latest repository. Run `python -m pytest -q` and verify current code/config; capture commit SHA.
2. Create an evaluation table (Unity Catalog Delta if permitted) containing the per-control audit rows above. Keep `ground_truth_key_affected` in a **restricted evaluation table** not exposed to model prompts.
3. Run development ablations A–F in notebooks; append run records. Use Genie to query only the analytics tables (for example: “For 30% correlated development runs, compare key-control miss recovery, surfaced AFFECTED+UNCERTAIN workload, and excluded key misses by experiment_id”).
4. Select one configuration using the frozen development criteria; record its commit, prompt hash, endpoint, top_k and all parameters. No test-driven iterative tuning.
5. Run the five-repeat full held-out test matrix and regenerate `output/` result files. Keep previous files intact or version results under an experiment ID.
6. Produce one compact summary: measured result, pass/fail for each gate, unresolved misses, review burden, stability, and recommendation (continue, revise, or lineage repair).

### Genie example questions after the evaluation table exists

- “Show recovery, baseline misses, hybrid misses and workload increase by degradation level and pattern for the same set of change IDs.”
- “For 30% change-correlated development experiments, which variants recover at least 50% of baseline key misses while adding at most 25% affected-plus-uncertain review items?”
- “Which key-control pairs were missed entirely by the surfaced output, and how many of those were sampled from the excluded list?”
- “What fraction of key-control decisions are identical across all five runs for each locked experiment?”
- “Compare the hybrid to the lineage-repair baseline at equivalent metadata-decay conditions.”

If Genie cannot access the tables, use a Databricks SQL notebook or SQL editor. Do not paste sensitive credentials into Genie prompts.

## Minimum deliverables

- Corrected hybrid aggregation and regression tests (UNAFFECTED excluded, UNCERTAIN counted, key misses visible).
- Development experiment ledger and recall-versus-workload frontier.
- Locked five-repeat test evaluation on the full held-out split.
- Reproducible per-control audit table and queryable summary.
- One-page result note that clearly distinguishes **observed** metrics from targets and recommendations.

**Current recommendation:** prioritize the aggregation bug and matched-case evaluation, then evidence-grounded retrieval/classification; do not label the current hybrid ready for pilot.
