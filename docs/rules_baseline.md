# Metadata-only rules baseline

The baseline is deliberately simple and auditable. It receives only the observable case.

## Algorithm
1. Start from the change ticket's structured changed-entity IDs.
2. Traverse visible directed dependency edges using the frozen propagating relationship set.
3. Stop at controls.
4. Rank reachable controls by:
   1. shortest hop distance;
   2. key-control status;
   3. control ID for deterministic tie-breaking.

No embeddings, semantic matching, LLM, hidden graph, or answer-key fields are used.

## Evaluation boundary
`scripts/baseline.py` is the system under test. It never imports ground-truth code.

`scripts/evaluate_baseline.py` is benchmark infrastructure and may load hidden labels solely to score predictions.

## Workload
For this baseline, every reachable recommended control counts as one reviewer item. There is no `UNCERTAIN` state.

## Reachability
If degradation removes every visible path to an affected key control, that pair is reported as unreachable. This is important: the hybrid's proposed value is specifically to recover some controls that structured metadata can no longer reach.

## Interpretation
At 0% degradation the baseline should normally have full key-control recall by construction. At 30% and 60%, especially under change-correlated damage, recall may fall. The hybrid must recover misses without exceeding the pre-registered workload threshold.
