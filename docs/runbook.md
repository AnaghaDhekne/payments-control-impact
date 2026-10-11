# Runbook

Run from the repository root with Python 3.12. Tests, benchmark generation, rules, and the offline demo do not require Databricks.

## Offline checks and demo

```bash
python -m pip install -r requirements-dev.txt
python -m pytest -q
python -m scripts.validate_graph
python -m scripts.run_dependency_review demo --output output/dependency_review_demo.json
python -m scripts.evaluate_baseline > output/baseline_results.json
```

The demo contains a hand-authored proposal and simulated approval. It is not a model evaluation.

## Export a development case

```bash
python -m scripts.export_case --change-id CHG-001 --output output/runs/development/case.json
```

This command removes the damage manifest. Do not include hidden labels in model inputs.

## Generate and review proposals

Install requirements-llm.txt and configure Databricks SDK authentication in your environment. The default endpoint is databricks-llama-4-maverick; confirm availability in your workspace. No credentials belong in this repository.

```bash
python -m pip install -r requirements-llm.txt
python -m scripts.run_dependency_review propose --case output/runs/development/case.json --output output/runs/development/proposals.json
```

For a saved response add `--response response.json`. Inspect exact quotations and whether each claimed DIRECT dependency follows from them. Write reviews.json as a list:

```json
[{"proposal_id": "copy-from-batch", "decision": "APPROVE", "reviewer": "your-name", "reviewed_at": "2026-10-11T23:00:00Z", "reason": "Explain why the documents establish this direct dependency"}]
```

Use REJECT or UNCERTAIN when appropriate. Pending proposals never alter the graph.

```bash
python -m scripts.run_dependency_review review --case output/runs/development/case.json --batch output/runs/development/proposals.json --reviews reviews.json --output output/runs/development/result.json
```

## Offline scoring

Independent labels must contain affected_control_ids, key_control_ids, and correct_proposal_ids. Do not show labels to the model or impact reviewer.

```bash
python -m scripts.score_dependency_review --result output/runs/development/result.json --labels labels.json --output output/runs/development/metrics.json
```

See [Phase 2 evaluation](dependency_review_phase2.md) for reviewer effort, proposal precision, recovery, provisional targets, and fresh-test requirements.

## Reproduce Phase 1

```bash
python -m scripts.generate_benchmark
python -m scripts.generate_observable
python -m scripts.evaluate_repair --split test
python -m scripts.evaluate_hybrid --split development --level 30 --mode correlated --runs 5 --top-k 30
```

Hybrid console output includes progress lines before JSON. Preserve raw output and configuration. Five runs are required to measure repeated-run agreement; single-run agreement is a placeholder. Existing test scenarios are historical and must not be treated as fresh Phase 2 validation.
