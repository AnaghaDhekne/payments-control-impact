# Payments Control Impact

When a payment field, rule, interface or report changes, which controls are
affected? Lineage metadata is often incomplete, so a rules-only walk of the
dependency graph misses controls. This proof of concept tests whether a
tool-using LLM agent (the **detective**) can recover those misses with cited
evidence, on a synthetic outbound cross-border payments benchmark with a known
answer key.

All data is synthetic. No real bank, customer or control inventory is used.

## Current status (2026-10-15)

The agentic path runs end to end on Databricks (`databricks-gpt-oss-120b`),
at 30% change-correlated metadata degradation:

| Measure | Tuned cases (4) | Unseen cases (8), code frozen | Gate |
|---|---|---|---|
| Key controls missed by rules, recovered | 22 of 27 (81.5%) | **32 of 49 (65.3%)** | >= 50%: met |
| Precision of newly recommended controls | 56 of 61 (91.8%) | **79 of 87 (90.8%)** | (no gate) |
| Added review items vs rules items | 102 vs 19 | **169 vs 38** | <= 25%: **not met** |
| Avoidable review items per case | not measured | **7.0** | (descriptive) |
| Key-control agreement over 5 runs | | running | >= 95%: open |

The unseen-case result is the one to quote; the tuned-case figure is
optimistic. Main weakness: review burden, from the agent over-claiming impact
across functional areas and the verifier rejecting links that are clear from
the text. Under way: an A/B test of a stricter agent (variant B), a five-run
consistency check, then one held-out run on the 18 test cases with the chosen
variant. Details, diagnosis and pre-registered plans:
[docs/results.md](docs/results.md).

## How it works

1. **Benchmark.** A hidden graph of 148 nodes (101 controls) and 238 edges, and 54 change
   scenarios (36 development, 18 test). Labels come from graph paths, not from
   any model.
2. **Degradation.** Each case exposes a damaged copy of the lineage (edges
   removed near the change) plus change tickets and control documents.
3. **Rules baseline.** Walks the visible edges from the changed entity.
4. **Detective.** An LLM chooses read-only tools (explore graph nodes, search
   and inspect controls), submits findings with exact quotes and a causal
   chain, and a second model call verifies each finding. Disagreements go to
   human review as UNCERTAIN. No inferred edges are written.
5. **Scoring.** Offline, against the hidden labels, which never reach the model.

See [docs/architecture.md](docs/architecture.md) and
[docs/evaluation.md](docs/evaluation.md).

## Quick start

Offline checks (no model, no credentials):

```bash
python -m pip install -r requirements-dev.txt
python -m pytest -q
python -m scripts.validate_graph
python -m scripts.evaluate_baseline > baseline_results.json
```

Live runs on Databricks are submitted as jobs so they survive closed terminals:

```bash
python -m pip install -r requirements-llm.txt
python -m scripts.detective_job submit \
    --repo /Workspace/Users/<you>/payments-control-impact \
    --change-ids CHG-001 CHG-014 \
    --output-dir /Volumes/workspace/default/detective_runs/<run-name>
python -m scripts.detective_job status <run_id>
```

Full instructions and troubleshooting: [docs/runbook.md](docs/runbook.md).

The results are presented in a Databricks App (`app/`): an executive summary,
context for newcomers, how it works, live evidence from the run files, a case
explorer, FAQ and a question box answered from the project documents. Deploy
with `python -m scripts.deploy_app` from a Databricks terminal.

## Repository layout

| Path | Contents |
|---|---|
| `scripts/detective.py` | The agent: tools, loop, verifier, resume |
| `scripts/databricks_llm.py` | Model-serving adapter (gpt-oss reply handling, retries) |
| `scripts/run_detective_suite.py` | Run and score cases; `--resume` |
| `scripts/detective_job.py`, `job_entry.py` | Submit and monitor runs as Databricks jobs |
| `scripts/run_detective.py` | Single-case run or exact replay of a saved transcript |
| `scripts/inspect_detective_run.py`, `probe_model.py` | Diagnose a run; check endpoint answer quality |
| `scripts/score_detective.py` | Offline scoring against labels |
| `scripts/baseline.py`, `evaluate_baseline.py` | Rules baseline and its evaluation |
| `scripts/generate_benchmark.py`, `generate_observable.py`, `ground_truth.py`, `validate_graph.py` | Benchmark and answer key |
| `scripts/case_io.py`, `export_case.py` | Observable-case helpers and export |
| `app/`, `scripts/deploy_app.py` | Databricks App presenting the POC (executive summary to case explorer); deploy script |
| `data/` | Hidden graph and change set ([data/README.md](data/README.md)) |
| `tests/` | Offline tests with scripted model responses |
| `archive/` | Earlier phases' raw results ([archive/README.md](archive/README.md)) |

The repository as it was before this cleanup, including earlier pipeline code
and documents, is preserved on the branch `pre-cleanup-2026-10-15`.
