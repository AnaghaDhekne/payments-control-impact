# Novelty Pitch — Why This Project Matters

Date: 2026-10-08
Project: Payments Control Impact
Purpose: One-page articulation of the project's core novelty and selling point for stakeholders.

## Elevator Pitch

**"Existing tools assume your metadata is perfect. It never is. We measure exactly what happens when it isn't — and whether AI can recover the gap."**

## The Problem Nobody Names

ServiceNow, Archer, LeanIX — they all traverse a dependency graph to tell you which controls are affected by a change. But they silently fail when the graph has missing or stale edges. Nobody talks about this because nobody tests for it.

In the real world, metadata degrades. Edges go stale. Documentation drifts. Controls get missed. Compliance blind spots appear without anyone knowing.

## What This Project Does

When the graph misses a control, an LLM reads the control's actual documentation and the change ticket, and reasons about whether it is affected — even without a graph edge connecting them. This is the "hybrid" approach: graph first, LLM second.

## Why It Is Credible, Not Hype

The project does not just say "AI helps." It quantifies:

- How many missed controls did the LLM recover? (recovery rate)
- How much extra review workload did it create? (workload increase)
- Under what degradation conditions? (6-condition matrix: 0/30/60% × random/correlated)
- Is it reproducible? (five-run agreement metric)
- Would just fixing the metadata be better than adding AI? (lineage repair comparator)

No vendor provides this. ServiceNow does not tell you "we missed 30% of your controls because your CMDB is stale." This project does.

## The One-Sentence Novelty

> This is the first system to quantitatively evaluate whether LLM-assisted narrative reasoning can recover controls missed by degraded dependency graphs in payment compliance — with pre-registered thresholds, workload accounting, and a lineage-repair baseline.

The novelty is not the graph, not the LLM, not the payment domain. It is the **rigorous evaluation of whether the combination provides net value under realistic data quality conditions**. That is what no industry system or academic benchmark does.

## What to Tell Stakeholders

> Every GRC tool on the market assumes your dependency metadata is complete and accurate. We know it isn't. This project measures the gap — and tests whether an LLM can close it without creating unacceptable review burden. If it can, we have a tool that works in the real world, not just in a perfect-metadata demo. If it can't, we know we need to fix our lineage first — and we have the numbers to justify that investment.

## Capability Matrix — What Industry Does vs. What This Project Does

| Question stakeholders ask | Industry systems | This project |
| --- | --- | --- |
| Does the AI actually help? | Not measured | Measured recovery rate under 6 degradation conditions |
| What does it cost me? | Not measured | Measured workload increase (extra controls to review) |
| Is it reliable? | Not measured | Five-run agreement metric — same answer every time? |
| What if we just fix our metadata instead? | Not asked | Lineage repair comparator (Experiment F) |
| When can we trust it? | Post-hoc claims | Pre-registered go/no-go thresholds |
| What did we miss? | Not reported | Excluded key misses — controls never surfaced |

## See Also

- [Industry Comparison](industry_comparison.md) — detailed vendor-by-vendor comparison with citations
- [Evaluation Improvement Plan](evaluation_improvement_plan.md) — pre-registered thresholds and experiment design
- [Project Reference](project_reference.md) — plain-language summary of all components

Source: assistant's analysis based on public product documentation and project requirements, October 2026.