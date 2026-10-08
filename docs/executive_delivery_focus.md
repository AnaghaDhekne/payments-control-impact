# Project positioning and delivery focus

Date: 2026-10-08

## Working title
Payments Control Impact: Evidence-Guided Impact Assessment for Payment Modernization

## Business problem
Payment-message modernization can affect sanctions, fraud, transaction monitoring, reconciliation and reporting controls. Change-impact assessments depend on system lineage, control mappings and narrative documents that may be incomplete, stale or inconsistent. A missing graph edge is **not** proof that a control is missing or failing: it is an evidence gap requiring investigation.

## Solution
Preserve the deterministic dependency graph as the baseline. When graph evidence is insufficient, retrieve relevant control documents and use an LLM to propose *evidence-supported candidate impacts*. Keep the three decisions separate: AFFECTED, UNCERTAIN and UNAFFECTED. Do not silently drop UNCERTAIN cases to reduce workload. Every newly surfaced control should include the changed payment attribute, potentially affected control activity, supporting text, evidence limitations, proposed review action and owner if available.

## Executive output
Deliver a practical **Change Impact Review Pack**, independent of whether the LLM passes the POC gate:
1. Change summary: impacted payment fields, systems, processes and control families.
2. Known impacts: controls reached by the existing dependency graph.
3. Additional potential impacts: AI-suggested controls with grounded evidence, clearly marked unverified.
4. Evidence gaps: missing/stale lineage and unresolved controls; distinguish uncertainty from confirmed compliance failures.
5. Prioritized review queue: key controls first, ranked by evidence strength and risk; display counts and owner/action.
6. Decision note: what to investigate, which metadata to repair, whether AI-assisted review offers net value, and whether the method meets the pre-registered gates.

## Current observed development result (not a pilot claim)
The latest summary reports 36 synthetic development cases, five runs at 30% correlated degradation: mean key-miss recovery 49.5%, additional reviewer workload 201.5%, and exact five-run key-decision agreement 85.9%. All three POC gates fail (>=50% recovery, <=25% workload, >=95% agreement). The referenced output/dev_30_correlated.json is currently empty in the repository; restore the complete audit artifact and independently recompute the metrics before using them as verified evidence. The 18-case held-out split has not been confirmed under a locked final configuration.

## Shortest implementation path
1. **Reproducibility first:** restore nonempty valid JSON audit output for the 36 development cases, including run, change ID, control ID, ground-truth label in evaluation-only data, baseline membership, retrieval membership, raw decision, evidence, final surfaced status, and reviewer workload. Validate aggregates.
2. **Evidence-guided retrieval:** implement a field-aware candidate scorer alongside the existing token-Jaccard baseline using only observable ticket and control-document fields. Compare top_k=20 and top_k=30 on development cases; report retrieval recall of affected key controls before LLM calls.
3. **Actionable output:** for each LLM-only AFFECTED or UNCERTAIN item, capture changed attribute, control dependency, quoted evidence fragment(s), and proposed action. Rank evidence-backed findings; preserve a counted uncertainty queue.
4. **One decision-oriented comparison:** compare existing graph, current corrected hybrid, and evidence-guided hybrid on matched development cases. Report key misses, recovery, total surfaced review count, false positives, uncertainty, five-run agreement and model calls. Plot or tabulate the recall-versus-workload trade-off. Do not tune on held-out tests.
5. **Executive pack:** generate one concise summary with known impacts, potential impacts, unknowns, top remediation actions, measured performance and go/no-go. Use only actual benchmark findings, not invented production impacts.
6. Freeze the strongest defensible development configuration; only then run the held-out test once. If no configuration meets the gate, recommend human review and lineage repair, not automated deployment.

## Differentiation without exaggerated novelty
Graph-based impact analysis, LLM compliance assistance and GRC dashboards exist. This POC's practical contribution is *evidence-guided recovery and prioritization of potential payment-control impacts when dependency metadata is degraded*, with an explicit safety/workload evaluation and an auditable executive review pack. Do not claim this is the first such system or that no commercial vendor addresses missing metadata.

## Acceptance criteria for a useful deliverable
- Reproducible, nonempty development results and matched baselines.
- Per-control trace from change attribute to candidate impact and supporting evidence.
- Separate known, potential and unknown impact categories.
- No suppression of uncertain items or hidden key misses to meet workload targets.
- A reviewer can take concrete actions from the output even if all LLM performance gates fail.
