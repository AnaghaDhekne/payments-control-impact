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
The manually inspectable seed graph is retained. Additional controls are attached to explicit payment-domain anchors across validation, screening, screening review, authorization, authorization monitoring, transformation, repair, reconciliation, break review, and reporting.

Change scenarios span field mappings, validation, screening-field selection, message mapping, thresholds, interfaces, reports, and systems.

## Limitation
Template expansion intentionally creates repeated control families. Before final evaluation, a payments/controls practitioner should review whether the graph and control distribution are credible enough for a POC. A negative review is a kill condition, not something to tune away.
