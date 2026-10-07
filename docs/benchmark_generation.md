# Benchmark generation

The benchmark is expanded with deterministic templates rather than LLM-generated answer-key content.

## Frozen scale
- 101 controls
- 54 change scenarios
- deterministic seed: `20261007`
- development/test assignment fixed at generation time
- held-out set must contain at least 40 affected (change, key-control) pairs

## Why deterministic templates?
The purpose is not to claim the synthetic control inventory reproduces a specific bank. It creates a controlled environment in which the relationship between a change and its affected controls is known independently of the model being evaluated.

LLMs may later generate or rewrite **narrative artifacts presented to the system**, but they do not determine the hidden graph or labels.

## Expansion approach
The manually inspectable seed graph is retained. Additional controls are attached to explicit payment-domain anchors across validation, screening, screening review, authorization, authorization monitoring, transformation, repair, reconciliation, break review, and reporting. Each generated control has two distinct, semantically related observable dependencies: a primary control-chain anchor (for example a governing system or evidence artifact) and an alternate dependency already present in that family’s business chain (for example its rule or report). This avoids making every generated control depend on a single metadata edge while preserving domain meaning.

Change scenarios span field mappings, validation, screening-field selection, message mapping, thresholds, interfaces, reports, and systems.

## Benchmark freeze\nAfter this topology-resilience revision and a successful integrity/baseline rerun, the hidden graph, change set, degradation seed, split, and answer-key semantics should be frozen before hybrid-model evaluation. Future changes should be limited to narrative realism or implementation defects and documented explicitly.\n\n## Limitation
Template expansion intentionally creates repeated control families. Before final evaluation, a payments/controls practitioner should review whether the graph and control distribution are credible enough for a POC. A negative review is a kill condition, not something to tune away.
