# Ground-truth labeling rules

These rules are frozen before synthetic narrative generation. The hidden graph determines whether a control is affected; explicit rules determine assurance actions.

## Stage 1 — affected vs unaffected
A control is affected when the changed entity reaches it through an allowed dependency path under benchmark impact semantics. A control is unaffected when no qualifying path exists, even when its text resembles an affected control.

This binary decision is the primary evaluation target.

## Stage 2 — multi-label actions

### REASSESS_DESIGN
Assign when a change alters an input, rule, system behavior, automation, scope, frequency, parameter, or dependency used by control logic.

### REFRESH_EVIDENCE
Assign when control design may remain valid but an artifact used to demonstrate operation changes—for example REPORT → EVIDENCE → CONTROL.

### OUT_OF_CYCLE_TEST
Assign when a key control's testing/evidence period spans a material implementation or rollback date, or a material automation/logic change makes pre-change testing insufficient for the post-change period.

### CONTROL_GAP_REVIEW
Human escalation, not an automatically designed control. Flag when a material new risk-bearing path has no adequate existing control in the complete ground-truth graph.

### UNCERTAIN
System output, not a ground-truth action. Use when exposed evidence is insufficient or contradictory. It counts as reviewer workload.

## Multi-label behavior
A screening-input mapping change may require REASSESS_DESIGN + REFRESH_EVIDENCE + OUT_OF_CYCLE_TEST. A report-format-only change may require REFRESH_EVIDENCE only.

## Required label record
Every ground-truth label stores change_id, control_id, affected, action labels, supporting graph paths, rule IDs, control criticality, and relevant implementation/test-period dates.

No LLM may create or modify benchmark ground truth.
