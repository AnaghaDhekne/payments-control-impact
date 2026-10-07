# Reproducible POC runbook

## What GitHub can validate without Databricks
The GitHub Actions **POC checks** workflow runs unit tests and the deterministic rules baseline on Python 3.12. It uploads the baseline result as a workflow artifact. No Databricks account, model serving endpoint, token, or secret is required. This is not a hybrid LLM evaluation.

## Running locally
```bash
python -m pip install -r requirements-dev.txt
python -m pytest -q
python -m scripts.evaluate_baseline > baseline_results.json
```

## Databricks hybrid evaluation (when access is available)
Install `databricks-sdk` and `openai` in the Databricks environment, and use an authenticated workspace with the `databricks-llama-4-maverick` serving endpoint.

Iterate only on development:
```bash
python -u -m scripts.evaluate_hybrid --split development --level 30 --mode correlated --runs 1 --top-k 20 > hybrid_development.json 2>&1
```

Once prompt, retrieval and parsing are locked, run held-out test explicitly:
```bash
python -u -m scripts.evaluate_hybrid --split test --level 30 --mode correlated --runs 5 --top-k 20 > hybrid_test.json 2>&1
```

The five-run stability metric is meaningful only with `--runs 5`. Never report a single-run placeholder as demonstrated stability. Inspect `parse_failure_count` in every run; a nonzero count invalidates an unqualified performance claim.

## Decision rule
At 30% correlated degradation: key-control miss recovery >=50%, incremental reviewer workload <=25%, and exact key-control prediction agreement >=95% over five runs. If the LLM does not beat the deterministic baseline within these constraints, recommend improving metadata/lineage rather than deploying GenAI.

## Limits
All entities and payment cases are synthetic. The repository does not contain real bank records, and no client deployment or financial benefit is demonstrated. A shadow-mode client pilot is required before making commercial claims.
