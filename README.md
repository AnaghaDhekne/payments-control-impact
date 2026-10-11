# Payments Control Impact

An experimental workflow for identifying payment controls affected by changes when dependency metadata is incomplete. All scenarios and records are synthetic.

## Current status

**Phase 2 is implemented; live development evaluation is next.** The LLM proposes missing direct dependencies with quoted evidence. A human reviews each proposal, approved links enter the graph, and rules rerun the impact list. The offline fixture demonstrates wiring, not AI accuracy.

Phase 1 did not meet the original held-out gates. Its [reported findings](docs/findings_and_gate_review.md) remain available, but final five-run raw artifacts need reconciliation before external claims. Phase 2 has no performance success claim yet.

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

1. [Architecture](docs/architecture.md): components and data boundaries.
2. [Runbook](docs/runbook.md): runnable commands and file formats.
3. [Phase 2 evaluation](docs/dependency_review_phase2.md): assumptions and provisional gates.
4. [Domain model](docs/domain_model.md) and [ground-truth rules](docs/ground_truth_rules.md).
5. [Contributing](CONTRIBUTING.md): maintenance and validation.

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
| docs/archive/ and output/archive/ | Historical plans and evidence |

## Benchmark and evidence

The original benchmark contains 101 controls and 54 scenarios, with 0%, 30%, and 60% metadata degradation under random and change-correlated damage. Phase 2 requires fresh scenario families for final evaluation. Matching a quote verifies provenance, not dependency correctness. Every reviewed proposal counts as work.

Generated observable datasets are excluded from version control. Recreate them with:

```bash
python -m scripts.generate_benchmark
python -m scripts.generate_observable
python -m scripts.evaluate_baseline > output/baseline_results.json
```

See the [output inventory](output/README.md) for artifact status. For live model calls install requirements-llm.txt and follow the runbook. Never commit credentials.
