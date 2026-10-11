# Architecture and data boundaries

## Current workflow

1. The CLI loads one observable case.
2. build_prompt selects change_id, ticket, visible metadata, and control documents; hidden labels and the degradation manifest are excluded.
3. The model proposes direct entity-to-control edges with exact source quotations.
4. validate_proposals checks IDs, relationships, duplicates, and quote provenance. Valid proposals remain PENDING; quote matching does not verify meaning.
5. A human records APPROVE, REJECT, or UNCERTAIN with reviewer, timestamp, and reason.
6. apply_reviews verifies the case digest, copies the graph, inserts approved edges, and reruns baseline.rank_controls.
7. The offline scorer compares outcomes with independent labels.

## File contracts

| File | Contents |
| --- | --- |
| Case | change_id, change_ticket, visible_metadata, control_documents |
| Batch | Case digest, proposals, raw response, validation rejections |
| Reviews | proposal_id, decision, reviewer, reviewed_at, reason |
| Result | Baseline/final paths, audit, pending IDs, repaired case |
| Offline labels | affected_control_ids, key_control_ids, correct_proposal_ids |

Proposal IDs bind the case digest and edge tuple. Changing the case invalidates old approvals. Reviewer identity is a user-entered audit field, not authenticated access control. Pending proposals do not establish that a control is unaffected.

## Runtime versus evaluation

Runtime modules consume observable information only. Benchmark generators and scorers may read hidden fixtures. Never expose hidden edges, removed-edge IDs, labels, or oracle approvals to the proposer or impact reviewer. Independent edge adjudication must distinguish direct dependency from indirect impact.

## Legacy experiments and limits

hybrid.py proposes impacts directly; evaluate_hybrid.py and evaluate_evidence.py score those recommendations. evaluate_repair.py restores known missing synthetic edges: an oracle comparator, not a practical repair process. Retain these modules for comparison.

Phase 2 currently repairs only direct non-control-to-control edges. All supplied documents enter one prompt; measure context size and response truncation before scaling. Stable approved-graph traversal does not establish repeatable model proposals. Measure proposal variation, human-review correctness, recovery, total review work, minutes, and cost separately.
