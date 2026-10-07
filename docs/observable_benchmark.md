# Observable benchmark views

The evaluated systems consume only artifacts under `data/observable/`. Hidden answer-key material remains under `data/ground_truth/`.

## Six conditions
- 0% random
- 0% change-correlated
- 30% random
- 30% change-correlated
- 60% random
- 60% change-correlated

At 0%, the two modes are intentionally equivalent in metadata removal. They remain separate files so the evaluation matrix is uniform.

## Metadata degradation

**Random** removes the requested percentage of exposable dependency edges using a deterministic per-change seed.

**Change-correlated** ranks edges by undirected graph distance to the changed entity and preferentially removes nearby relationships with deterministic tie-breaking. A local-frontier guard limits removal around each changed entity to the requested degradation fraction and retains at least one exposable incident relationship when one exists. This prevents 30% degradation from mechanically isolating every changed entity while still making newly changed neighborhoods less reliable than the rest of the graph.

The hidden graph itself is never modified.

## Narrative degradation

Each case contains a change ticket and control documents. Depending on level and deterministic seed, text may receive:
- legacy aliases/stale terminology;
- an omitted sentence;
- selected misleading `control impact: N/A` language.

A degradation manifest records every operation for auditability. The manifest is benchmark metadata and should not be supplied to the evaluated model.

## Leakage rule

Observable artifacts must never contain hidden labels such as `affected`, `actions`, `supporting_paths`, or `rule_ids`. Tests enforce this boundary.

## Important limitation

The current text degradation is intentionally mechanical. Before final model evaluation, narrative generation should be improved to create more realistic tickets/procedures while preserving the frozen graph and labels. Narrative realism can change; answer-key semantics cannot.
