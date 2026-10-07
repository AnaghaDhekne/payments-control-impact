# Pre-registered evaluation contract

## Methods

### Rules baseline
Uses only exposed structured metadata/dependency edges. Candidates are ranked by shortest hop distance from the changed entity with deterministic tie-breaking. If missing metadata prevents the baseline from reaching a target recall, report **unreachable**.

### Hybrid
Uses the same deterministic candidate generation plus semantic retrieval over exposed narrative artifacts and structured control-level LLM assessment. It must never access the complete hidden graph.

## Degradation grid
Evaluate 0%, 30%, and 60% degradation under:
1. **Random** — eligible metadata relationships are removed/staled with fixed seeded sampling.
2. **Change-correlated** — relationships nearest changed/new/renamed entities are preferentially removed or made stale.

Narratives degrade in parallel: missing mentions, legacy aliases, stale system names, incomplete descriptions, and misleading self-reported "no impact" statements. Seeds/configuration are recorded.

## Metrics
Primary: affected vs unaffected control detection, with **key-control recall over affected (change, key-control) pairs** as the executive safety metric.

Secondary: criticality-weighted recall, precision/false positives, multi-label action accuracy/F1, uncertain rate, grounding correctness, consistency, latency/model usage.

Reviewer workload is `recommended_controls + uncertain_controls`, compared within the same degradation condition.

At 0% degradation, recall parity is expected. Measure whether semantic expansion adds false positives/workload.

## Frozen decision threshold
At **30% change-correlated degradation**, proceed only if the hybrid:
1. recovers **≥50% of key-control misses** made by rules;
2. requires **≤25% additional reviewer workload** versus rules at that degradation level; and
3. achieves **≥95% agreement** on affected/unaffected classification for key controls across **five runs**.

Target zero observed hybrid key-control misses, but report sample size and uncertainty. With zero misses among n affected (change, key-control) pairs, report the approximate 95% upper miss-rate bound as `3/n`.

## Kill conditions
Do not recommend a GenAI pilot if thresholds fail, key-control outputs remain materially inconsistent, a qualified controls/payments reviewer finds the dependency model materially unrealistic, or healthy metadata already makes deterministic selection sufficient.

## Benchmark hygiene
Separate development/test changes; never tune prompts on held-out labels; freeze graph, rules, degradation seeds and test IDs before final evaluation; never regenerate hard cases after failures; report negative results.
