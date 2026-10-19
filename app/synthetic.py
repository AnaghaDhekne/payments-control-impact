"""The synthetic benchmark, prepared for display: tables, maps and a worked example.

Everything here is computed offline from the benchmark generators. Nothing is
sent to a model. Maps are Graphviz DOT strings rendered by st.graphviz_chart.
"""

from __future__ import annotations

from collections import Counter
from functools import lru_cache

TYPE_ORDER = [
    "DATA_ELEMENT",
    "RULE",
    "INTERFACE",
    "SYSTEM",
    "PROCESS",
    "REPORT",
    "EVIDENCE",
    "CONTROL",
]
TYPE_LABEL = {
    "DATA_ELEMENT": "Data elements",
    "RULE": "Rules",
    "INTERFACE": "Interfaces",
    "SYSTEM": "Systems",
    "PROCESS": "Processes",
    "REPORT": "Reports",
    "EVIDENCE": "Evidence",
    "CONTROL": "Controls",
}
TYPE_ROLE = {
    "DATA_ELEMENT": "Payment fields that a change touches (names, addresses, amount, currency, status, screening result)",
    "RULE": "Business logic that uses the fields: address validation, approval threshold, screening field-set, message mapping",
    "INTERFACE": "Connections in and out: initiation API, screening request, outbound CBPR+, settlement and ledger feeds",
    "SYSTEM": "Applications: orchestration, validation, screening, risk, authorization, transformation, reconciliation, reporting",
    "PROCESS": "Stages of the payment flow; context for the agent, almost no links",
    "REPORT": "Exception and break reports that reviewers work from",
    "EVIDENCE": "Review sign-offs that show a control was performed",
    "CONTROL": "What the POC is about: 11 hand-written parent controls and 90 family variants",
}
# Light fills that stay readable on Streamlit's white graph background.
FILL = {
    "DATA_ELEMENT": "#EEEDFE",
    "RULE": "#E6F1FB",
    "INTERFACE": "#E1F5EE",
    "SYSTEM": "#E1F5EE",
    "PROCESS": "#F1EFE8",
    "REPORT": "#FAEEDA",
    "EVIDENCE": "#FAEEDA",
    "CONTROL": "#FBEAF0",
}
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
FAMILY_SEPARATOR = " — "


@lru_cache(maxsize=1)
def benchmark():
    """Graph, changes and answer key (labels computed by plain graph code)."""
    from scripts.evaluate_baseline import _truth_by_change
    from scripts.generate_benchmark import build_changes, build_graph

    graph, changes = build_graph(), build_changes()
    return graph, changes, _truth_by_change(graph, changes)


@lru_cache(maxsize=8)
def condition(level=30, mode="correlated"):
    """Damaged cases for one condition, keyed by change ID."""
    from scripts.generate_observable import build_condition

    graph, changes, _ = benchmark()
    return {
        c["change_id"]: c for c in build_condition(graph, changes, level, mode)["cases"]
    }


def nodes_by_id():
    graph, _, _ = benchmark()
    return {n["id"]: n for n in graph["nodes"]}


def is_family(node):
    return node["type"] == "CONTROL" and FAMILY_SEPARATOR in node.get("name", "")


def type_counts():
    graph, _, _ = benchmark()
    c = Counter(n["type"] for n in graph["nodes"])
    return [
        {"Item type": TYPE_LABEL[t], "Count": c[t], "What it is": TYPE_ROLE[t]}
        for t in TYPE_ORDER
    ]


def link_counts():
    graph, _, _ = benchmark()
    c = Counter(e["relationship"] for e in graph["edges"])
    meaning = {
        "DEPENDS_ON": "A control depends on a system, rule or report",
        "GOVERNED_BY": "A system or rule is governed by a control (or rule by system)",
        "EVIDENCES": "Evidence shows a control was performed",
        "USES": "A rule uses a data element; a process uses a system",
        "FEEDS": "Data or a system feeds the next system, process or report",
        "PRODUCES": "A system or report produces data, a report or evidence",
        "VALIDATES": "A rule validates a system's input",
        "COMPENSATED_BY": "A manual fallback control; does not carry impact",
    }
    return [
        {
            "Link type": r,
            "Count": n,
            "Carries impact": "yes" if r in PROPAGATING else "no",
            "Meaning": meaning.get(r, ""),
        }
        for r, n in c.most_common()
    ]


def control_table():
    graph, _, _ = benchmark()
    rows = []
    for n in graph["nodes"]:
        if n["type"] != "CONTROL":
            continue
        fam = n["name"].split(FAMILY_SEPARATOR)
        rows.append(
            {
                "Control": n["id"],
                "Name": n["name"],
                "Criticality": n.get("criticality", ""),
                "Kind": "family variant" if len(fam) > 1 else "parent",
                "Family": fam[0],
            }
        )
    return rows


def change_table():
    _, changes, truth = benchmark()
    nodes = nodes_by_id()
    rows = []
    for c in changes:
        t = truth[c["change_id"]]
        aff = [k for k, v in t.items() if v.affected]
        rows.append(
            {
                "Change": c["change_id"],
                "Title": c["title"],
                "Changed item": ", ".join(
                    f"{i} {nodes[i]['name']}" for i in c["changed_node_ids"]
                ),
                "Split": c["split"],
                "Affected controls": len(aff),
                "of which key": sum(1 for k in aff if t[k].criticality == "KEY"),
            }
        )
    return rows


def example(change_id, level=30, mode="correlated"):
    """Everything about one change: ticket, answer key, damage, rules result."""
    from scripts.baseline import rank_controls

    graph, changes, truth = benchmark()
    nodes = nodes_by_id()
    case = condition(level, mode)[change_id]
    t = truth[change_id]
    affected = sorted(k for k, v in t.items() if v.affected)
    key = [k for k in affected if t[k].criticality == "KEY"]
    rules = {r["control_id"] for r in rank_controls(case)}
    removed = set(case["degradation_manifest"]["removed_edge_ids"])
    edges = {e["id"]: e for e in graph["edges"]}
    path_edges = set()
    rows = []
    for k in affected:
        path = t[k].supporting_paths[0]
        hops = list(zip(path, path[1:]))
        broken = []
        for a, b in hops:
            eid = next(
                (
                    e["id"]
                    for e in graph["edges"]
                    if e["source"] == a
                    and e["target"] == b
                    and e["relationship"] in PROPAGATING
                ),
                None,
            )
            if eid:
                path_edges.add(eid)
                if eid in removed:
                    broken.append(f"{a}→{b}")
        rows.append(
            {
                "Control": k,
                "Name": nodes[k]["name"],
                "Key": "key" if k in key else "",
                "Path in the complete map": " → ".join(path),
                "Links hidden at this level": ", ".join(broken) or "none",
                "Rules method finds it": "yes" if k in rules else "no",
            }
        )
    rows.sort(key=lambda r: (r["Key"] != "key", r["Control"]))
    exposable = [e for e in graph["edges"] if e.get("metadata_exposable", True)]
    return {
        "case": case,
        "change": next(c for c in changes if c["change_id"] == change_id),
        "affected": affected,
        "key": key,
        "rules_found": sorted(rules),
        "rules_found_affected": sorted(rules & set(affected)),
        "key_misses": sorted(set(key) - rules),
        "rows": rows,
        "removed": removed,
        "path_edges": path_edges,
        "removed_on_paths": sorted(path_edges & removed),
        "edges_total": len(graph["edges"]),
        "edges_exposable": len(exposable),
        "edges_visible": len(case["visible_metadata"]["edges"]),
        "edges": edges,
    }


def _q(s):
    return '"' + str(s).replace("\\", "\\\\").replace('"', "'") + '"'


def _short(name, n=26):
    return name if len(name) <= n else name[: n - 1] + "…"


def map_dot(
    highlight=None,
    removed=frozenset(),
    show="complete",
    focus=None,
    changed=frozenset(),
    affected=frozenset(),
):
    """DOT for the whole map (148 items, 238 links) or a focused subset.

    show = "complete": every link drawn as in the hidden map.
           "damaged": links removed for the selected change are not drawn.
           "overlay": removed links drawn red and dashed.
    focus = optional set of node IDs to restrict the drawing to.
    changed / affected = node IDs to emphasise for a selected change.
    """
    graph, _, _ = benchmark()
    nodes = [n for n in graph["nodes"] if focus is None or n["id"] in focus]
    ids = {n["id"] for n in nodes}
    lines = [
        "digraph G {",
        'graph [rankdir=LR, newrank=true, nodesep=0.08, ranksep=0.9, fontname="Helvetica", bgcolor="white"];',
        'node [shape=box, style="rounded,filled", fontname="Helvetica", fontsize=9, height=0.25, margin="0.06,0.02", color="#B4B2A9", penwidth=0.6];',
        'edge [color="#B4B2A9", arrowsize=0.4, penwidth=0.6];',
    ]
    for t in TYPE_ORDER:
        group = [n for n in nodes if n["type"] == t]
        if t == "CONTROL":
            parents = [n for n in group if not is_family(n)]
            family = [n for n in group if is_family(n)]
            groups = [("controls_parent", parents), ("controls_family", family)]
        else:
            groups = [(t.lower(), group)]
        for gname, members in groups:
            if not members:
                continue
            lines.append(f"subgraph {gname} {{ rank=same;")
            for n in members:
                fill = FILL[n["type"]]
                pen = 0.6
                font = "#2C2C2A"
                if n["id"] in changed:
                    fill, pen = "#F0997B", 2.0
                elif n["id"] in affected:
                    fill, pen = "#ED93B1", 1.4
                label = f"{n['id']}  {_short(n.get('name', ''))}"
                tip = f"{n['id']} {n.get('name', '')} ({TYPE_LABEL[n['type']]}"
                if n.get("criticality"):
                    tip += f", {n['criticality'].lower()}"
                tip += f"): {n.get('description', '')}"
                lines.append(
                    f"{_q(n['id'])} [label={_q(label)}, tooltip={_q(tip)}, fillcolor={_q(fill)}, penwidth={pen}, fontcolor={_q(font)}];"
                )
            lines.append("}")
    for e in graph["edges"]:
        if e["source"] not in ids or e["target"] not in ids:
            continue
        gone = e["id"] in removed
        if gone and show == "damaged":
            continue
        attrs = {"tooltip": f"{e['source']} {e['relationship']} {e['target']}"}
        style = []
        if not e.get("metadata_exposable", True):
            attrs["color"] = "#888780"
            style.append("dotted")
        if e["relationship"] not in PROPAGATING:
            style.append("dotted")
        if gone and show == "overlay":
            attrs["color"] = "#E24B4A"
            attrs["penwidth"] = "1.6"
            style.append("dashed")
        elif highlight and e["id"] in highlight:
            attrs["color"] = "#185FA5"
            attrs["penwidth"] = "1.4"
        if style:
            attrs["style"] = ",".join(dict.fromkeys(style))
        a = ", ".join(f"{k}={_q(v)}" for k, v in attrs.items())
        lines.append(f"{_q(e['source'])} -> {_q(e['target'])} [{a}];")
    lines.append("}")
    return "\n".join(lines)


def focus_nodes(ex):
    """Items on the answer-key paths of one change, plus their direct neighbours on those paths."""
    _, _, truth = benchmark()
    t = truth[ex["change"]["change_id"]]
    keep = set(ex["change"]["changed_node_ids"])
    for k in ex["affected"]:
        keep.update(t[k].supporting_paths[0])
    return keep


def degradation_by_distance(ex):
    """Removed links by distance from the changed item (undirected steps)."""
    from scripts.generate_observable import undirected_distance

    graph, _, _ = benchmark()
    dists = [undirected_distance(graph, s) for s in ex["change"]["changed_node_ids"]]

    def d(e):
        return min(min(x.get(e["source"], 99), x.get(e["target"], 99)) for x in dists)

    rows = Counter()
    for e in graph["edges"]:
        if not e.get("metadata_exposable", True):
            continue
        bucket = min(d(e), 4)
        rows[(bucket, e["id"] in ex["removed"])] += 1
    out = []
    for b in range(5):
        kept, gone = rows[(b, False)], rows[(b, True)]
        if kept + gone:
            out.append(
                {
                    "Distance from the change": (
                        "4 or more steps"
                        if b == 4
                        else f"{b} step{'s' if b != 1 else ''}"
                    ),
                    "Links": kept + gone,
                    "Removed": gone,
                    "Kept": kept,
                    "Share removed": f"{100 * gone / (kept + gone):.0f}%",
                }
            )
    return out
