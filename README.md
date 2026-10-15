# Payments Control Impact

An experimental workflow for identifying payment controls affected by changes when dependency metadata is incomplete. All scenarios and records are synthetic.

## Current status

**Detective agentic path runs live on Databricks (development results only).**
On four development cases it recovered 22 of 27 key controls missed by the
rules baseline (81.5%) with 92% precision on new controls; the workload gate is
not met and consistency is not yet measured. See
[live results](docs/detective_live_results.md) and
[the diagnosis and run commands](docs/detective_recovery.md).
The saved impact-discovery run reports 57.6% recovery and 91.2% new-control
precision, but only 25.3% direct-edge precision. The separate simulated LLM
review reports 5.6% recovery and 27.3% approval precision. These studies measure
different decisions; the passing impact result does not establish successful
reviewed dependency reconstruction. The new tool-using detective investigates
control impact without inserting invented direct edges.

**Historical Phase 2 impact results:** The AI system
proposes missing dependency edges with cited evidence, mechanically validates
them, and supports human review. On 18 held-out test cases (30% correlated
degradation, 5-run ensemble), it achieves 57.6% key-miss recovery (gate: 50%)
and 91.2% precision (gate: 80%). Results are oracle-adjudicated; human review
has not been conducted. See the [final report](docs/final_report.md).

Phase 1 did not meet the original held-out gates. Its [reported findings](docs/findings_and_gate_review.md) remain available as historical reference.
Lineage repair (75% recovery, 99.1% precision) remains the recommended primary
strategy; AI is supplementary where lineage cannot be repaired.

## Quick start — Python 3.12

Run from the repository root:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements-dev.txt
python -m pytest -q
python -m scripts.run_dependency_review demo --output output/dependency_review_demo.json
```

On Windows use `.venv/Scripts/Activate.ps1` in PowerShell. Open the demo JSON to compare the baseline, proposal evidence, simulated approval, and final impact path. No Databricks access is needed.

## Reading order

1. [Final report](docs/final_report.md): held-out evaluation results and recommendations.
2. [Architecture](docs/architecture.md): components and data boundaries.
3. [Runbook](docs/runbook.md): runnable commands and file formats.
4. [Phase 2 evaluation](docs/dependency_review_phase2.md): workflow design and current status.
5. [Domain model](docs/domain_model.md) and [ground-truth rules](docs/ground_truth_rules.md).
6. [Contributing](CONTRIBUTING.md): maintenance and validation.

## Repository map

| Location | Purpose |
| --- | --- |
| scripts/dependency_proposals.py | Observable-only prompt, validation, approval, impact rerun |
| scripts/run_dependency_review.py | Demo and file-based commands |
| scripts/score_dependency_review.py | Offline scoring against independent labels |
| scripts/baseline.py | Directed metadata traversal shared by both phases |
| scripts/hybrid.py and evaluate_*.py | Phase 1 methods and comparisons |
| scripts/generate_*.py | Reproducible synthetic benchmark generation |
| scripts/ground_truth.py | Hidden answer-key engine; evaluation only |
| data/ground_truth/ | Seed fixtures and frozen benchmark snapshots |
| data/observable/ | Generated inputs, recreated locally |
| tests/ | Graph, evaluation, parsing, and approval checks |
| docs/ and output/archive/ | Documentation and historical evidence |

## Benchmark and evidence

The original benchmark contains 101 controls and 54 scenarios, with 0%, 30%, and 60% metadata degradation under random and change-correlated damage. Phase 2 requires fresh scenario families for final evaluation. Matching a quote verifies provenance, not dependency correctness. Every reviewed proposal counts as work.

Generated observable datasets are excluded from version control. Recreate them with:

```bash
python -m scripts.generate_benchmark
python -m scripts.generate_observable
python -m scripts.evaluate_baseline > output/baseline_results.json
```

See the [output inventory](output/README.md) for artifact status. For live model calls install requirements-llm.txt and follow the runbook. Never commit credentials.
