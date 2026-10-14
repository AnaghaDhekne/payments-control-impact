# Remaining work — Payments Control Impact

Updated: 2026-10-13. The POC execution checklist (Sections 0–8) is complete;
held-out evaluation passed both Phase 2 gates. The items below are the
remaining work needed before production consideration. See [final report](docs/final_report.md)
for current status.

## Human review
- [ ] Conduct blinded human review of a sample of proposals (without hidden labels)
- [ ] Measure reviewer accuracy, time per review, and disagreement rates
- [ ] Test adversarial cases: stale narratives, legacy names, no lexical overlap, conflicting evidence, new entities
- [ ] Validate audit trails, case-version integrity, rollback of mistaken edges

## Code quality
- [ ] Add unit/integration tests for quote matching, edge direction, invalid JSON, abstentions, empty retrieval, stale-batch binding
- [ ] Ensure scripts have module docstrings, clear types, meaningful errors, and no hard-coded case-specific shortcuts
- [ ] Set up CI for tests, formatting/linting, and static checks (no Databricks access needed)
- [ ] Extract inline pipeline code to reusable scripts before deployment

## Reproducibility
- [ ] Create a fresh Python 3.12 environment, install pinned requirements, run `python -m pytest -q`
- [ ] Add a one-command offline replay script that fails loudly if artifacts are missing
- [ ] Add results provenance table mapping each claim to commit, config, dataset split, command, artifact path
- [ ] Run a clean-clone setup and offline replay from the README; fix any failing commands

## Documentation
- [ ] Audit legacy docs (findings_and_gate_review.md, executive_summary_final.md, runbook.md) for stale numbers
- [ ] Update architecture diagram, runbook, contribution guide, and troubleshooting
- [ ] Add C06 dynamic detection (currently uses static case list)

## Evaluation
- [ ] Compare Phase 2 against lineage repair using clearly specified repair rates and fair conditions
- [ ] Compare Phase 2 vs Phase 1 ranking approach as baseline on the same cases
- [ ] Regenerate raw dev artifacts with persistent storage (ephemeral /tmp artifacts lost)


