# Maintaining the project

Use Python 3.12. Run commands from the repository root after installing requirements-dev.txt.

## Checks before committing

```bash
python -m black --check scripts tests
python -m pytest -q
python -m scripts.validate_graph
python -m scripts.evaluate_baseline > output/baseline_results.json
python -m scripts.run_dependency_review demo --output output/dependency_review_demo.json
```

Format with `python -m black scripts tests`. Comments should explain assumptions, data boundaries, and tradeoffs. Document public function inputs and outputs.

Historical evidence belongs in output/archive. New evaluated runs need a unique directory under output/runs containing configuration, commit SHA, case IDs, raw responses, reviews, and metrics. Generated datasets, caches, virtual environments, and credentials are not source.

Never import hidden answer-key modules into runtime proposal code. Keep labels separate from model inputs and human impact review. Freeze criteria before testing on fresh scenario families; preserve earlier results.
