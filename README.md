# Payments Control Impact

When a payment field, rule, interface or report changes, which controls are
affected? Lineage metadata is often incomplete, so a rules-only walk of the
dependency graph misses controls. This proof of concept tests whether a
tool-using LLM agent (the **detective**) can recover those misses with cited
evidence, on a synthetic outbound cross-border payments benchmark with a known
answer key.

All data is synthetic. No real bank, customer or control inventory is used.

## Current status (2026-10-18)

The agentic path runs end to end on Databricks (`databricks-gpt-oss-120b`).
Every test below was registered in [docs/results.md](docs/results.md) before
it ran.

### Expectations: met and not met

| Expectation | Target | Result | Status |
|---|---|---|---|
| Agentic path works end to end on Databricks | runs, logged, replayable | Live jobs; every step logged | **Met** |
| Find key controls the rules miss (held-out, 18 cases) | >= 50% | **113 of 144 (78.5%; 95% CI 71–84%)** | **Met** |
| Precision of newly recommended controls (held-out) | (no gate) | 262 of 280 (93.6%) | Good |
| Added review workload vs rules | <= 25% | 406 vs 64 items (held-out) | Not met; unreachable by any method that meets the line above |
| Unnecessary review items (held-out, version A) | (descriptive) | 4.2 per change | Weakness |
| Same key decision on repeat runs (version A, 5 runs) | >= 95% | 80% | **Not met** |
| Fix 1 (version B, cited chain required) | pre-registered rule | no wrong flags, but recall 55% | Rejected |
| Fix 2 (version C + 3-run vote), fresh-damage test: recovery | >= 50%, within 5 pts of A | 52.7% vs A 50.0% | Met |
| Fix 2: unnecessary review items | <= 3 per change and below A | **0.33 vs A 0.61** | **Met** |
| Fix 2: two independent votes agree | >= 95% | **94.4%** (153 of 162; 154 needed) | **Not met**; C not adopted, A stays |
| Ready for production | | synthetic data, no practitioner review | No; next step is a practitioner review |

The stop rule agreed in advance (held-out recovery below 50%) was not
triggered. Weak spot on the held-out run: screening-engine changes (5 of 20).
Version C fixes review noise and narrows the consistency gap (single runs
agree 90.8%, votes 94.4%) at about four times A's model cost.

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
