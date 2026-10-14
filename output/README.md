# Output inventory

| Location | Status |
| --- | --- |
| dependency_review_demo.json | Hand-authored Phase 2 wiring fixture; simulated approval |
| heldout_run/ | Held-out evaluation raw artifacts: per-run pickles, merged results, review study outputs |
| archive/baseline_results.json | Historical deterministic baseline |
| archive/dev_30_correlated*.json | Historical development experiment artifacts |
| archive/hybrid_matrix*.json | Older Phase 1 evaluations; superseded for final gate decisions |
| archive/result_summary_and_actions.txt | Historical summary; may use superseded thresholds |
| runs/ | Ignored local work directory for new experiments |

Held-out evaluation (2026-10-13) is complete: 18 test cases, 5-run ensemble,
both Phase 2 gates pass (recovery 57.6%, precision 91.2%). Raw per-run pickles
and merged results are in heldout_run/. Note: pickle files are gitignored (large
binaries); heldout_results.json is also gitignored — regenerate via the frozen
protocol if needed. See [docs/final_report.md](../docs/final_report.md) for details.

Keep each new run's raw responses, proposals, human reviews, case IDs, configuration, commit SHA, and metrics together. Publish reviewed, synthetic evidence deliberately; never publish credentials or real customer data. Generated datasets and scratch outputs are ignored by default.
