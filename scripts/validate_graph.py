"""Validate structural integrity of the hidden dependency graph.

This validator checks graph mechanics only. It does not implement impact semantics;
those are intentionally added separately after the graph is manually reviewed.
"""
from __future__ import annotations
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GRAPH = ROOT / "data" / "ground_truth" / "payment_graph_v0_1.json"

NODE_TYPES = {"PROCESS","SYSTEM","INTERFACE","DATA_ELEMENT","RULE","REPORT","EVIDENCE","CONTROL"}
EDGE_TYPES = {"USES","PRODUCES","FEEDS","TRANSFORMS","VALIDATES","SCREENS","EVIDENCES","GOVERNED_BY","DEPENDS_ON","COMPENSATED_BY"}

def validate(path: Path = GRAPH) -> dict:
    data = json.loads(path.read_text(encoding="utf-8"))
    nodes = data["nodes"]
    edges = data["edges"]
    node_ids = [n["id"] for n in nodes]
    edge_ids = [e["id"] for e in edges]

    errors = []
    duplicate_nodes = [k for k,v in Counter(node_ids).items() if v > 1]
    duplicate_edges = [k for k,v in Counter(edge_ids).items() if v > 1]
    if duplicate_nodes: errors.append(f"duplicate node IDs: {duplicate_nodes}")
    if duplicate_edges: errors.append(f"duplicate edge IDs: {duplicate_edges}")

    known = set(node_ids)
    for n in nodes:
        if n["type"] not in NODE_TYPES:
            errors.append(f"{n['id']}: invalid node type {n['type']}")
        if n["type"] == "CONTROL" and "criticality" not in n:
            errors.append(f"{n['id']}: control missing criticality")

    for e in edges:
        if e["relationship"] not in EDGE_TYPES:
            errors.append(f"{e['id']}: invalid relationship {e['relationship']}")
        if e["source"] not in known:
            errors.append(f"{e['id']}: unknown source {e['source']}")
        if e["target"] not in known:
            errors.append(f"{e['id']}: unknown target {e['target']}")
        if e["source"] == e["target"]:
            errors.append(f"{e['id']}: self-loop")

    controls = [n for n in nodes if n["type"] == "CONTROL"]
    key_controls = [n for n in controls if n.get("criticality") == "KEY"]
    return {
        "valid": not errors,
        "errors": errors,
        "node_count": len(nodes),
        "edge_count": len(edges),
        "control_count": len(controls),
        "key_control_count": len(key_controls),
        "node_types": dict(sorted(Counter(n["type"] for n in nodes).items())),
        "edge_types": dict(sorted(Counter(e["relationship"] for e in edges).items())),
    }

if __name__ == "__main__":
    result = validate()
    print(json.dumps(result, indent=2))
    raise SystemExit(0 if result["valid"] else 1)
