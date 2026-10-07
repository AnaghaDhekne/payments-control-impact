# Hidden ground truth

Files in this directory are the benchmark answer key. They are used to generate labels and degraded evaluation views, but must **not** be made available to the rules baseline, retrieval index, LLM prompt, or application at evaluation time.

- `payment_graph_v0_1.json` — complete synthetic dependency graph
- `seed_changes.json` — manually inspectable seed changes used while validating semantics

The final benchmark will freeze a larger graph, change set, action rules, degradation seeds, and held-out IDs before final evaluation.
