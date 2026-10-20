# Payments Control Impact

When a payment field, rule, interface or report changes, which controls are
affected? Lineage metadata is often incomplete, so a rules-only walk of the
dependency graph misses controls. This proof of concept tests whether a
tool-using LLM agent (the **detective**) can recover those misses with cited
evidence, on a synthetic outbound cross-border payments benchmark with a known
answer key.

All data is synthetic. No real bank, customer or control inventory is used.

## Current status (2026-10-19): final, version A

The agentic path runs end to end on Databricks (`databricks-gpt-oss-120b`).
Every test below was registered in [docs/results.md](docs/results.md) before
it ran.

### Expectations: met and not met

| Expectation | Target | Result | Status |
|---|---|---|---|
| Agentic path works end to end on Databricks | runs, logged, replayable | Live jobs; every step logged | **Met** |
| Find key controls the rules miss (held-out, 18 cases) | >= 50% | **113 of 144 (78.5%; 95% CI 71–84%)** | **Met** |
| Precision of newly recommended controls (held-out) | (no gate) | 262 of 280 (93.6%) | Good |
| Additional review volume vs rules (not wasted effort) | <= 25% | 406 additional items beyond 64 baseline items; 331 affected, 75 unaffected | Original volume gate not met; counts useful recoveries too |
| Unaffected additional review items (held-out, version A) | (descriptive) | 75 total; 4.2 per change; 18.5% of additional items | Review overhead, identified using synthetic labels |
| Same key decision on repeat runs (version A, 5 runs) | >= 95% | 80% | **Not met** |
| Fix 1 (version B, cited chain required) | pre-registered rule | no wrong flags, but recall 55% | Rejected |
| Fix 2 (version C + 3-run vote), fresh-damage test: recovery | >= 50%, within 5 pts of A | 52.7% vs A 50.0% | Met |
| Fix 2: unnecessary review items | <= 3 per change and below A | **0.33 vs A 0.61** | **Met** |
| Fix 2: two independent votes agree | >= 95% | **94.4%** (153 of 162; 154 needed) | **Not met**; C not adopted, A stays |
| Fix 3 (version D = A + tie-break), final bounded round, 5 dev cases x 2 runs | recovery >= A; unaffected items, undecided, repeatability not worse | recovery 18 vs 20 of 32; unaffected items 16 vs 30; undecided 0 vs 0; repeatability 76% vs 76% | **Not adopted** (recovery lower); A stays |
| Ready for production | | synthetic data, no practitioner review | No; next step is a practitioner review |

### Version A: what the additional review contains

The 406 items are **additional controls to consider, not 406 incorrect findings**.
They are beyond the rules baseline's 64 items (470 total items including the baseline).

| Additional items | Affected in the synthetic answer key | Unaffected | Total |
|---|---:|---:|---:|
| New recommendations | 262 | 18 | 280 |
| UNCERTAIN, requiring human assessment | 69 | 57 | 126 |
| **Total** | **331 (81.5%)** | **75 (18.5%)** | **406** |

The 331 affected items represent useful additional coverage that warrants review;
the 75 unaffected items represent review overhead on this benchmark. Uncertainty
alone does not mean a finding is wrong. The affected/unaffected breakdown uses
offline synthetic labels, which a real reviewer would not have in advance.
The original +25% gate measures item volume, including correct recoveries; it
remains failed, but does not measure wasted effort or elapsed review time.
Only confirmed recommendations count toward key-miss recovery; the 69 affected
UNCERTAIN items are not counted as recovered.

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

## The client experience (Databricks App)

The POC is presented as an investigation experience (`app/web`), served by a
standard-library Python server (`app/server.py`, the command in `app.yaml`).
It opens on a short plain-language landing page (`#/home`, `app/web/js/home.js`):
the problem, how the product works from inputs to human decisions, where it
fits in a bank, what is proven and not, how a bank would adopt it, and the
example change (CHG-027) set up without its result, so the walkthrough keeps
its reveal. A separate product overview (`#/overview`) holds the example
finding and the measured results; every figure there is
read from the same exported results. `tests/test_home_page.py` checks this in a
browser where Playwright is installed. Two reference areas sit in the header: the **evidence room** (results, all 18
test changes, limits and fixes tried, Ask) and the **technical handbook**
(architecture, benchmark and scoring, how the map is damaged, the investigator
and verifier calls with their exact prompts, reproduction). The walkthrough covers five moments on any of the 18 held-out changes (flagship:
CHG-027, a screening-interface change the lineage check clears; all 20 affected
controls are recommended, with full-phrase evidence):

1. **The change**: the change record and the reassuring conventional assessment.
2. **The blind spot**: an interactive dependency map, switching between what the
   lineage records and what is actually connected; the reveal traces one key
   control and names its missing link, and any other control can be clicked.
3. **The investigation**: a step-by-step replay of the recorded agent run (not a
   live model call); click a control for its evidence: the quoted ticket and
   procedure text, the agent's and the independent checker's reasoning, the
   routing and a proposed reviewer action. The answer key is hidden until asked.
4. **The consequence**: the same 101 controls seen by the check, by the
   investigation and by the ground truth; all 162 key-control impacts; review
   workload (331 of 406 added items are genuinely affected); consistency; the one
   silent miss.
5. **The decision**: what is demonstrated, what is uncertain, what to validate
   before a pilot, and the options.

An **evidence room** holds the method, results, every test change with every
decision, the pre-registered version tests, architecture, limits,
reproduction steps and a question box answered from the project documents.

Every figure comes from `python -m scripts.build_experience_data`, which exports
`app/web/data` from the benchmark code and the recorded run archive;
`tests/test_experience_data.py` checks the export against the archive. Run
locally with `python app/server.py` (http://localhost:8000). Deploy from the
repository root with the Deploy button or `python -m scripts.deploy_app`.

The earlier Streamlit workbench remains available for local use:
`streamlit run app/app.py`.

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
| `app/web`, `app/server.py`, `scripts/build_experience_data.py` | Client experience (HTML, CSS, JavaScript modules), its server and its data export |
| `app/app.py`, `scripts/deploy_app.py` | Earlier Streamlit workbench; deploy script |
| `data/` | Hidden graph and change set ([data/README.md](data/README.md)) |
| `tests/` | Offline tests with scripted model responses |
| `archive/` | Earlier phases' raw results ([archive/README.md](archive/README.md)) |

The repository as it was before this cleanup, including earlier pipeline code
and documents, is preserved on the branch `pre-cleanup-2026-10-15`.
