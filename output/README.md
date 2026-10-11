# Output inventory

| Location | Status |
| --- | --- |
| dependency_review_demo.json | Hand-authored Phase 2 wiring fixture; simulated approval |
| archive/baseline_results.json | Historical deterministic baseline |
| archive/dev_30_correlated*.json | Historical development experiment artifacts |
| archive/hybrid_matrix*.json | Older Phase 1 evaluations; superseded for final gate decisions |
| archive/result_summary_and_actions.txt | Historical summary; may use superseded thresholds |
| runs/ | Ignored local work directory for new experiments |

Final Phase 1 five-run development/test and repair artifacts are not clearly present. Documentation reports final metrics, but they require reconciliation before external claims. Archiving preserves available evidence; it does not certify those metrics.

Keep each new run's raw responses, proposals, human reviews, case IDs, configuration, commit SHA, and metrics together. Publish reviewed, synthetic evidence deliberately; never publish credentials or real customer data. Generated datasets and scratch outputs are ignored by default.
