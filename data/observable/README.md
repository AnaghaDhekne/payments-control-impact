# Generated observable inputs

Run `python -m scripts.generate_benchmark` then `python -m scripts.generate_observable` from the repository root to recreate the six deterministic condition files. Generated JSON is ignored to avoid committing duplicated datasets.

These files include a degradation_manifest for evaluator diagnostics. Use `python -m scripts.export_case` to export development cases without that manifest for model input. Never expose removed-edge IDs or hidden graph fixtures to the proposer.
