# Archive

Raw outputs from earlier phases, kept for reference. The code that produced
them is not on `main`; it is preserved, with the original reports, on the
branch `pre-cleanup-2026-10-15`. Summaries are in
[docs/results.md](../docs/results.md#earlier-phases-archived).

## `phase1/` — hybrid retrieval and ranking (2026-10-07/08)

| File | Contents |
|---|---|
| `result_summary_and_actions.txt` | Development results, 36 cases × 5 runs, `databricks-llama-4-maverick` |
| `dev_30_correlated.json`, `dev_30_correlated_fieldaware.json` | Development evaluation outputs |
| `baseline_results.json` | Rules-baseline evaluation at that time |
| `hybrid_matrix.json`, `hybrid_matrix_remaining.json` | Degradation-grid runs (`hybrid_matrix.json` is empty) |

## `phase2/` — dependency-edge proposals (2026-10-11/13)

| File | Contents |
|---|---|
| `heldout_run/heldout_results.json` | 18 held-out cases, 5-run ensemble: gates, summary, per-case results |
| `heldout_run/*.pkl` | Per-run raw model outputs (Python pickles; load only in a trusted environment) |
| `heldout_run/review_study_results.json`, `review_study_report.md` | Simulated LLM-as-reviewer study |
| `dependency_review_demo.json` | Hand-written wiring fixture with simulated approval; not a result |
| `Payments Control Impact.lvdash.json` | Databricks dashboard definition over the Phase 2 tables |
