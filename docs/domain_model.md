# Synthetic outbound cross-border payment domain

## Flow boundary
The benchmark models one fictional bank's outbound cross-border payment flow:
1. payment instruction
2. message/data validation
3. sanctions screening
4. fraud and limit checks
5. dual authorization
6. message transformation/enrichment
7. outbound dispatch
8. acknowledgements and exception/repair handling
9. nostro / GL reconciliation
10. operational/regulatory reporting

## Hidden graph node types
- PROCESS — business/process step
- SYSTEM — application/service
- INTERFACE — integration/message boundary
- DATA_ELEMENT — payment/message field
- RULE — validation/business rule
- REPORT — operational/regulatory report
- EVIDENCE — artifact relied on by a control
- CONTROL — control activity

## Relationships
USES, PRODUCES, FEEDS, TRANSFORMS, VALIDATES, SCREENS, EVIDENCES, GOVERNED_BY, DEPENDS_ON, COMPENSATED_BY.

Edges carry source/target, relationship, validity dates, and whether the relationship is exposed as metadata.

## Control families
Input/message validation; sanctions screening; fraud/limits; authorization; transformation/interface completeness; reconciliation; exceptions; reporting; relevant IT/interface controls. Controls are KEY, STANDARD, or SUPPORTING.

## Change families
The 50–60 changes span structured-address/field mappings, validation rules, transaction limits, reports/evidence, interfaces, aliases/renames, decommissions, shared interfaces, control automation/parameters, rollbacks, interacting release changes, and cosmetic/no-impact changes.

## Required adversarial cases
- ticket claims "control impact: N/A" when controls are affected
- stale retired system names
- new canonical name vs old narrative alias
- indirect two/three-hop dependencies
- textually similar unaffected controls
- evidence-only impact
- conflicting narrative and metadata
- shared-interface fan-out
- compensating controls
- numeric threshold changes
- rollback mid-period

Cases are fixed before the evaluated workflow is developed.
