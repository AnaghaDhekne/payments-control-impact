"""Deterministically expand the seed payment graph into the benchmark dataset.

No LLM is used. The generated controls/change scenarios come from explicit,
reviewable domain templates so the benchmark answer key is reproducible.
"""

from __future__ import annotations
import json, random
from copy import deepcopy
from pathlib import Path

try:
    ROOT = Path(__file__).resolve().parents[1]
except NameError:
    ROOT = Path.cwd().parent
SEED_GRAPH = ROOT / "data" / "ground_truth" / "payment_graph_v0_1.json"
OUT_GRAPH = ROOT / "data" / "ground_truth" / "payment_graph_benchmark.json"
OUT_CHANGES = ROOT / "data" / "ground_truth" / "benchmark_changes.json"
SEED = 20261007

CONTROL_TEMPLATES = [
    ("validation", "C01", "Required-field validation", "KEY"),
    ("screening", "C02", "Sanctions screening execution", "KEY"),
    ("screening_review", "C03", "Sanctions alert review", "KEY"),
    ("authorization", "C04", "Required payment authorization", "KEY"),
    ("auth_monitor", "C05", "Authorization exception monitoring", "STANDARD"),
    ("mapping", "C06", "Outbound transformation completeness", "KEY"),
    ("repair", "C07", "Reject and repair review", "STANDARD"),
    ("reconciliation", "C08", "Settlement and ledger reconciliation", "KEY"),
    ("break_review", "C09", "Aged reconciliation-break review", "STANDARD"),
    ("reporting", "C10", "Operational report completeness review", "STANDARD"),
]

# Each domain instance adds a control connected to an existing anchor. This makes
# expansion realistic enough for impact paths while preserving manual inspectability.
EXPANSIONS = [
    # family, primary anchor/relationship, alternate anchor/relationship.
    # Alternate anchors represent a distinct documented dependency already present
    # in the same control chain; they are not duplicate edges or arbitrary bypasses.
    ("validation", "S02", "GOVERNED_BY", "R01", "DEPENDS_ON"),
    ("screening", "S03", "GOVERNED_BY", "R03", "DEPENDS_ON"),
    ("screening_review", "E01", "EVIDENCES", "RP01", "DEPENDS_ON"),
    ("authorization", "S05", "GOVERNED_BY", "R02", "DEPENDS_ON"),
    ("auth_monitor", "E04", "EVIDENCES", "RP04", "DEPENDS_ON"),
    ("mapping", "S06", "GOVERNED_BY", "R04", "DEPENDS_ON"),
    ("repair", "E02", "EVIDENCES", "RP02", "DEPENDS_ON"),
    ("reconciliation", "E03", "EVIDENCES", "RP03", "DEPENDS_ON"),
    ("break_review", "E03", "EVIDENCES", "RP03", "DEPENDS_ON"),
    ("reporting", "S08", "GOVERNED_BY", "I04", "DEPENDS_ON"),
]

QUALIFIERS = [
    "daily completeness",
    "high-risk corridor",
    "priority payment",
    "manual override",
    "after-hours processing",
    "currency-specific",
    "high-value transaction",
    "repair queue",
    "weekend processing",
    "release monitoring",
]

CHANGE_TEMPLATES = [
    ("D03", "FIELD_MAPPING", "Debtor town-name mapping change"),
    ("D04", "FIELD_MAPPING", "Debtor country-code mapping change"),
    ("D07", "FIELD_MAPPING", "Creditor town-name mapping change"),
    ("D08", "FIELD_MAPPING", "Creditor country-code mapping change"),
    ("R01", "VALIDATION_RULE", "Structured-address validation rule change"),
    ("R03", "SCREENING_FIELD_SET", "Screening field-set change"),
    ("R04", "MESSAGE_MAPPING", "Outbound message mapping change"),
    ("R02", "PARAMETER_CHANGE", "High-value approval threshold change"),
    ("I02", "INTERFACE_CHANGE", "Screening interface change"),
    ("I03", "INTERFACE_CHANGE", "Outbound network interface change"),
    ("RP01", "REPORT_CHANGE", "Screening exception report change"),
    ("RP02", "REPORT_CHANGE", "Payment reject report change"),
    ("RP03", "REPORT_CHANGE", "Reconciliation report change"),
    ("RP04", "REPORT_CHANGE", "Authorization exception report change"),
    ("S03", "SYSTEM_CHANGE", "Screening engine change"),
    ("S06", "SYSTEM_CHANGE", "Transformation service change"),
    ("I04", "INTERFACE_CHANGE", "Settlement-status feed change"),
    ("I05", "INTERFACE_CHANGE", "Ledger-posting feed change"),
]


def load_seed():
    return json.loads(SEED_GRAPH.read_text(encoding="utf-8"))


def build_graph():
    graph = deepcopy(load_seed())
    existing = {n["id"] for n in graph["nodes"]}
    next_control = 12
    next_edge = max(int(e["id"][1:]) for e in graph["edges"]) + 1

    # 10 families x 9 additional controls = 90 + original 11 = 101 controls.
    for family, anchor, rel, alternate_anchor, alternate_rel in EXPANSIONS:
        base = next(t for t in CONTROL_TEMPLATES if t[0] == family)
        for i in range(9):
            cid = f"C{next_control:03d}"
            next_control += 1
            qualifier = QUALIFIERS[i]
            criticality = base[3] if i < 4 else ("STANDARD" if i < 8 else "SUPPORTING")
            graph["nodes"].append(
                {
                    "id": cid,
                    "type": "CONTROL",
                    "name": f"{base[2]} — {qualifier}",
                    "description": f"Synthetic {qualifier} control in the {family.replace('_',' ')} family.",
                    "criticality": criticality,
                    "family": family,
                }
            )
            graph["edges"].append(
                {
                    "id": f"E{next_edge:03d}",
                    "source": anchor,
                    "target": cid,
                    "relationship": rel,
                    "direct": True,
                    "metadata_exposable": True,
                }
            )
            next_edge += 1
            graph["edges"].append(
                {
                    "id": f"E{next_edge:03d}",
                    "source": alternate_anchor,
                    "target": cid,
                    "relationship": alternate_rel,
                    "direct": True,
                    "metadata_exposable": True,
                }
            )
            next_edge += 1
    graph["version"] = "0.3.0"
    graph["generator_seed"] = SEED
    return graph


def build_changes():
    rng = random.Random(SEED)
    changes = []
    # 54 total: three deterministic variants of 18 meaningful templates.
    dates = ["2026-11-14", "2026-12-01", "2027-01-15"]
    for cycle in range(3):
        for idx, (node, ctype, title) in enumerate(CHANGE_TEMPLATES, start=1):
            n = len(changes) + 1
            changes.append(
                {
                    "change_id": f"CHG-{n:03d}",
                    "title": f"{title} — release {cycle+1}",
                    "changed_node_ids": [node],
                    "change_type": ctype,
                    "implementation_date": dates[cycle],
                    "material": True,
                    "release_group": f"R{cycle+1}",
                    "split": "test" if n % 3 == 0 else "development",
                }
            )
    # Stable shuffle changes order only; IDs and split remain fixed.
    rng.shuffle(changes)
    return changes


def main():
    graph = build_graph()
    changes = build_changes()
    OUT_GRAPH.write_text(json.dumps(graph, indent=2) + "\n", encoding="utf-8")
    OUT_CHANGES.write_text(json.dumps(changes, indent=2) + "\n", encoding="utf-8")
    controls = [n for n in graph["nodes"] if n["type"] == "CONTROL"]
    print(
        json.dumps(
            {
                "controls": len(controls),
                "key_controls": sum(n.get("criticality") == "KEY" for n in controls),
                "changes": len(changes),
                "test_changes": sum(c["split"] == "test" for c in changes),
                "seed": SEED,
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
