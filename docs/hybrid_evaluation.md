# Hybrid GenAI evaluation

The hybrid system is separated from hidden ground truth.

## Runtime flow
1. Run the deterministic metadata baseline.
2. Retrieve control narratives against the observable change ticket.
3. Send only the ticket, baseline IDs, and retrieved control documents to the LLM.
4. Require structured affected/unaffected/uncertain recommendations.
5. Union baseline recommendations with LLM AFFECTED or UNCERTAIN recoveries.
6. Score only in a separate evaluator that may load hidden labels.

The degradation manifest is audit metadata and must never be included in prompts.

## Workload
Reviewer workload is unique baseline recommendations plus LLM AFFECTED/UNCERTAIN recoveries. This prevents recall gains from simply returning every control.

## Benchmark freeze
Do not change the hidden graph, truth rules, split, degradation algorithm, or seed in response to hybrid-model results.
