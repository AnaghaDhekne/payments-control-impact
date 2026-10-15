"""Deterministic hidden-ground-truth impact engine.

The evaluated rules/GenAI systems must never import this module. It operates on the
complete hidden graph and produces benchmark labels.
"""

from __future__ import annotations
from collections import defaultdict, deque
from dataclasses import dataclass
from datetime import date
import json
from pathlib import Path
from typing import Iterable

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_GRAPH = ROOT / "data" / "ground_truth" / "payment_graph_v0_1.json"

# Relationships that can propagate a business/technology change downstream.
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
# COMPENSATED_BY is deliberately absent: a compensating-control link is contextual,
# not proof that the compensating control is impacted by every change to the primary.


@dataclass(frozen=True)
class Change:
    change_id: str
    changed_node_ids: tuple[str, ...]
    change_type: str
    implementation_date: str
    material: bool = True
    rollback_date: str | None = None


@dataclass
class ImpactLabel:
    change_id: str
    control_id: str
    affected: bool
    actions: list[str]
    supporting_paths: list[list[str]]
    rule_ids: list[str]
    criticality: str | None


def load_graph(path: Path = DEFAULT_GRAPH) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _adjacency(graph: dict) -> dict[str, list[dict]]:
    adj = defaultdict(list)
    for edge in graph["edges"]:
        if edge["relationship"] in PROPAGATING:
            adj[edge["source"]].append(edge)
    return adj


def qualifying_paths(
    graph: dict, starts: Iterable[str], max_hops: int = 6
) -> dict[str, list[list[str]]]:
    """Return shortest qualifying node paths from changed nodes to controls.

    Traversal is directed and relation-constrained. We keep shortest paths only so
    ground truth remains explainable and avoids arbitrary graph flooding.
    """
    nodes = {n["id"]: n for n in graph["nodes"]}
    adj = _adjacency(graph)
    found: dict[str, list[list[str]]] = defaultdict(list)
    best_control_depth: dict[str, int] = {}

    for start in starts:
        if start not in nodes:
            raise ValueError(f"unknown changed node: {start}")
        q = deque([(start, [start])])
        best_node_depth = {start: 0}
        while q:
            current, path = q.popleft()
            depth = len(path) - 1
            if depth >= max_hops:
                continue
            for edge in adj.get(current, []):
                nxt = edge["target"]
                new_path = path + [nxt]
                nd = depth + 1
                node = nodes[nxt]
                if node["type"] == "CONTROL":
                    previous = best_control_depth.get(nxt)
                    if previous is None or nd < previous:
                        best_control_depth[nxt] = nd
                        found[nxt] = [new_path]
                    elif nd == previous and new_path not in found[nxt]:
                        found[nxt].append(new_path)
                    continue
                # Prevent cycles while allowing an equally short alternate path.
                prev = best_node_depth.get(nxt)
                if prev is None or nd <= prev:
                    best_node_depth[nxt] = nd
                    q.append((nxt, new_path))
    return dict(found)


def _path_node_types(path: list[str], nodes: dict[str, dict]) -> list[str]:
    return [nodes[x]["type"] for x in path]


def _actions_for(
    control: dict,
    paths: list[list[str]],
    change: Change,
    nodes: dict[str, dict],
    test_period_start: str | None,
    test_period_end: str | None,
) -> tuple[list[str], list[str]]:
    actions: set[str] = set()
    rules: set[str] = set()

    for path in paths:
        types = _path_node_types(path, nodes)
        # Evidence/report-led impact: changed artifact or path entering a control
        # through evidence implies evidence refresh.
        if "EVIDENCE" in types or (types[0] == "REPORT" and types[-1] == "CONTROL"):
            actions.add("REFRESH_EVIDENCE")
            rules.add("GT-A2-EVIDENCE")

        # Logic/design impact. A change that reaches a control without passing
        # through evidence is treated as a control-design/input dependency change.
        if "EVIDENCE" not in types:
            actions.add("REASSESS_DESIGN")
            rules.add("GT-A1-DESIGN")

    # Key controls spanning a material implementation/rollback require additional
    # testing consideration. Dates are explicit inputs, never inferred by an LLM.
    if (
        control.get("criticality") == "KEY"
        and change.material
        and test_period_start
        and test_period_end
    ):
        start = date.fromisoformat(test_period_start)
        end = date.fromisoformat(test_period_end)
        impl = date.fromisoformat(change.implementation_date)
        rollback = (
            date.fromisoformat(change.rollback_date) if change.rollback_date else None
        )
        if start <= impl <= end or (rollback and start <= rollback <= end):
            actions.add("OUT_OF_CYCLE_TEST")
            rules.add("GT-A3-PERIOD")

    return sorted(actions), sorted(rules)


def label_change(
    graph: dict,
    change: Change,
    *,
    test_period_start: str | None = None,
    test_period_end: str | None = None,
) -> list[ImpactLabel]:
    nodes = {n["id"]: n for n in graph["nodes"]}
    paths = qualifying_paths(graph, change.changed_node_ids)
    labels = []
    for control in sorted(
        (n for n in graph["nodes"] if n["type"] == "CONTROL"), key=lambda x: x["id"]
    ):
        cpaths = paths.get(control["id"], [])
        affected = bool(cpaths)
        actions, rule_ids = (
            _actions_for(
                control, cpaths, change, nodes, test_period_start, test_period_end
            )
            if affected
            else ([], [])
        )
        labels.append(
            ImpactLabel(
                change_id=change.change_id,
                control_id=control["id"],
                affected=affected,
                actions=actions,
                supporting_paths=cpaths,
                rule_ids=rule_ids,
                criticality=control.get("criticality"),
            )
        )
    return labels
