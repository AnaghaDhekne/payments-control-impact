"""Metadata-only deterministic baseline.

Consumes an observable case only. It has no access to hidden graph or labels.
"""

from __future__ import annotations
from collections import defaultdict, deque

PROPAGATING = {
    "USES",
    "PRODUCES",
    "FEEDS",
    "TRANSFORMS",
    "VALIDATES",
    "SCREENS",
    "GOVERNED_BY",
    "DEPENDS_ON",
    "EVIDENCES",
}


def rank_controls(observable_case: dict) -> list[dict]:
    """Return ranked reachable controls and shortest observed paths. No hidden labels are read."""
    meta = observable_case["visible_metadata"]
    nodes = {n["id"]: n for n in meta["nodes"]}
    adj = defaultdict(list)
    for e in meta["edges"]:
        if e["relationship"] in PROPAGATING:
            adj[e["source"]].append(e["target"])
    # Edge direction models downstream impact; compensating links do not propagate.
    starts = observable_case["change_ticket"]["changed_entity_ids"]
    best = {}
    q = deque((s, 0, [s]) for s in starts if s in nodes)
    seen = {(s, 0) for s in starts}
    while q:
        cur, d, path = q.popleft()
        for nxt in sorted(adj.get(cur, [])):
            nd = d + 1
            np = path + [nxt]
            if nodes[nxt]["type"] == "CONTROL":
                prev = best.get(nxt)
                if prev is None or nd < prev["distance"]:
                    best[nxt] = {
                        "control_id": nxt,
                        "distance": nd,
                        "path": np,
                        "criticality": nodes[nxt].get("criticality"),
                    }
                continue
            marker = (nxt, nd)
            if nd <= 6 and marker not in seen:
                seen.add(marker)
                q.append((nxt, nd, np))
    return sorted(
        best.values(),
        key=lambda x: (
            x["distance"],
            0 if x["criticality"] == "KEY" else 1,
            x["control_id"],
        ),
    )
