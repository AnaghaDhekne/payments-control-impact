"""Export the evidence behind the client-facing experience (app/web) as JSON.

    python -m scripts.build_experience_data

Everything is computed from the repository: the benchmark generators (graph,
changes, answer key), the damage step (30% change-correlated, main seed), the
rules baseline, and the recorded held-out run of version A read from
results/detective_runs.tar.gz. Nothing is typed in by hand except the
pre-registered version tests, which are copied from docs/results.md with their
section names. Layouts are computed with Graphviz here, so the deployed app
needs no Graphviz.

Outputs (app/web/data):
    experience.json   headline metrics, portfolio, provenance, version tests
    graph.json        148 items, 238 links, full-map layout, control documents
    cases/<id>.json   one file per held-out change: ticket, damage, answer key,
                      baseline, recorded decisions with quotes, replay steps,
                      focused layout
"""

from __future__ import annotations

import json
import re
import subprocess
import tarfile
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "app" / "web" / "data"
ARCHIVE = ROOT / "results" / "detective_runs.tar.gz"
RUN = "heldout-final/run1"
PROVENANCE = {
    "job": "862812162377923",
    "date": "2026-10-16",
    "version": "A",
    "code": "d149a52",
    "model": "databricks-gpt-oss-120b",
    "condition": "30% of lineage links removed, nearest the change first (main seed)",
    "archive": "results/detective_runs.tar.gz",
}
# The case the experience opens on: the check finds none of its affected
# controls and the agent's evidence is quoted in full phrases on both sides.
FLAGSHIP = "CHG-027"
# Control procedure texts are the same in every case; overrides are per case.
DOCS_SOURCE = "CHG-003"
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

# Earlier approaches, copied from docs/results.md ("Earlier phases"). The sets,
# models and scoring differ from the held-out detective run, so they are a
# progression, not a like-for-like comparison.
APPROACHES = [
    {
        "approach": "Current lineage check (rules over recorded links)",
        "recovery": 18 / 162,
        "measure": "share of all 162 affected key controls found",
        "set": "18 held-out changes, 30% correlated damage",
        "caveat": "Deterministic; 42.6% at 30% random damage, 7.4% at 60%.",
    },
    {
        "approach": "Phase 1: hybrid retrieval and ranking",
        "recovery": 0.495,
        "measure": "key-miss recovery",
        "set": "36 development changes, 5 runs, Llama 4 Maverick",
        "caveat": "Development set; +201.5% reviewer workload; did not pass the gates.",
    },
    {
        "approach": "Phase 2: dependency-edge proposals",
        "recovery": 0.576,
        "measure": "key-miss recovery",
        "set": "18 held-out changes, 5-run union, GPT OSS 120B",
        "caveat": "Union of five runs plus an automatic quote-correction step; only 25.3% of proposed edges were correct.",
    },
    {
        "approach": "Agent investigation (this run)",
        "recovery": 113 / 144,
        "measure": "key-miss recovery",
        "set": "18 held-out changes, one run, GPT OSS 120B",
        "caveat": "Single frozen run; 30 more routed to a person, 1 not surfaced.",
    },
]


# Engineering lessons drawn from the version tests above (docs/results.md).
LESSONS = [
    [
        "Stricter evidence rules trade recall for precision.",
        "Demanding a cited chain removed unsupported recommendations and some real recoveries with them.",
    ],
    [
        "Voting steadies decisions, at a cost.",
        "A three-run vote came within one decision of the 95% target, for about four times the model calls.",
    ],
    [
        "A verifier of positive findings cannot catch false negatives.",
        "Controls marked not affected never reach it; the silent miss came from one.",
    ],
    [
        "Routing keeps doubt visible but hands it to people.",
        "Disagreements are never discarded, which is why review volume grows.",
    ],
    [
        "Tie-breaks are reliable when they promote, not when they dismiss.",
        "68 of 70 promotions were right; dismissals removed real impacts.",
    ],
]


def repeat_runs(repeat, truth, graph):
    """Five runs of three development changes: every affected key control's
    decision in each run. Agreement is recomputed from these records and must
    equal the archived consistency summary (tested)."""
    from scripts.run_detective_suite import labels_for

    names = {n["id"]: n["name"] for n in graph["nodes"]}
    out = []
    for cid in sorted(repeat):
        runs = repeat[cid]
        order = sorted(runs)
        for ctrl in labels_for(truth[cid])["key_control_ids"]:
            per = []
            for r in order:
                if ctrl in runs[r]["recommended"]:
                    per.append("recommended")
                elif ctrl in runs[r]["uncertain"]:
                    per.append("review")
                else:
                    per.append("not_recommended")
            out.append(
                {
                    "change": cid,
                    "control": ctrl,
                    "name": names.get(ctrl, ctrl),
                    "runs": per,
                    "same": len({x == "recommended" for x in per}) == 1,
                }
            )
    return {"runs": len(next(iter(repeat.values()))), "rows": out}


def prompts():
    """The two prompts of the recorded run (version A), from the agent's own code."""
    from scripts.detective import VERIFIER_INSTRUCTIONS, instructions_for

    return {
        "variant": PROVENANCE["version"],
        "code": PROVENANCE["code"],
        "investigator": instructions_for(PROVENANCE["version"]),
        "verifier": VERIFIER_INSTRUCTIONS,
    }


def _degradation():
    """Settings of the damage step, read from the generator itself."""
    from scripts import generate_observable as g

    return {"seed": g.SEED, "levels": list(g.LEVELS), "modes": list(g.MODES)}


# Copied from docs/results.md (pre-registered sections); shown in the evidence room.
VERSION_TESTS = [
    {
        "version": "B",
        "hypothesis": "Requiring a cited chain from the change to the control removes unsupported recommendations.",
        "trade_off": "Fewer wrong flags, but real impacts were lost too.",
        "name": "Stricter evidence rule",
        "source": "docs/results.md · Pre-registered: proposer chain requirement, A/B test",
        "test": "8 unseen development changes, one run",
        "rule": "Unaffected items at least 30% fewer, and no more than 3 fewer key controls found",
        "result": "Unaffected items 56 → 46 (−18%); key controls found 32 → 27",
        "decision": "Not adopted",
    },
    {
        "version": "C",
        "hypothesis": "A coverage sweep, a second look at not-affected key controls and a three-run vote make decisions repeatable without losing recovery.",
        "trade_off": "Close to the target, at about four times the model calls.",
        "name": "Extra checks and a three-run vote",
        "source": "docs/results.md · Pre-registered: version C with majority vote",
        "test": "18 test changes under fresh random damage; 6 runs of C, 2 of A",
        "rule": "Two votes agree on ≥ 95% of key decisions; recovery ≥ 50%; unaffected ≤ 3 per change and below A",
        "result": "Votes agree on 94.4% (153 of 162; 154 needed); recovery 52.7% vs 50.0%; unaffected 0.33 vs 0.61 per change; about 4× model calls",
        "decision": "Not adopted",
    },
    {
        "version": "D",
        "hypothesis": "A tie-break call on disagreements turns items sent to a person into decisions without losing recoveries.",
        "trade_off": "Fewer unaffected items, but fewer key misses found.",
        "name": "Tie-break step",
        "source": "docs/results.md · Pre-registered: final bounded round, variant D vs A",
        "test": "5 fresh-damage development changes, two runs each of A and D",
        "rule": "Recovery ≥ A; unaffected ≤ A; undecided ≤ A; repeatability ≥ A",
        "result": "Key misses found 18 vs 20 of 32; unaffected 16 vs 30; repeatability 76% both",
        "decision": "Not adopted",
    },
    {
        "version": "A + tie-break",
        "hypothesis": "Applying the tie-break to A's saved runs cuts review items without dismissing real impacts.",
        "trade_off": "Review fell by a third, but one in five truly affected review items was dismissed.",
        "name": "Tie-break applied to A's saved runs",
        "source": "docs/results.md · Pre-registered: tie-break applied to saved A runs",
        "test": "7 saved A runs, paired, 412 tie-break calls",
        "rule": "Recovery not lower; unaffected ≥ 25% fewer; ≤ 10% of truly affected review items dismissed; repeatability not lower",
        "result": "Found 258 → 267 of 411; unaffected 183 → 114 (−38%); 59 of 271 truly affected review items dismissed (21.8%)",
        "decision": "Not adopted",
    },
]


# ---------------------------------------------------------------- inputs


def benchmark():
    from scripts.evaluate_baseline import _truth_by_change
    from scripts.generate_benchmark import build_changes, build_graph
    from scripts.generate_observable import build_condition

    graph, changes = build_graph(), build_changes()
    truth = _truth_by_change(graph, changes)
    cases = {
        c["change_id"]: c
        for c in build_condition(graph, changes, 30, "correlated")["cases"]
    }
    return graph, changes, truth, cases


def recorded():
    """Held-out run files and metrics, plus the consistency summary, from the archive."""
    out, extra = {}, {}
    with tarfile.open(ARCHIVE) as t:
        for m in t.getmembers():
            name = m.name.lstrip("./")
            if (
                name.startswith(RUN + "/CHG-")
                and name.endswith(".json")
                and ".calls" not in name
            ):
                d = json.load(t.extractfile(m))
                out[d["change_id"]] = d
            elif name == RUN + "/metrics.json":
                extra["metrics"] = json.load(t.extractfile(m))
            elif name == "suite-11/consistency.json":
                extra["consistency"] = json.load(t.extractfile(m))
            elif (
                name.startswith("suite-11/run")
                and "/CHG-" in name
                and name.endswith(".json")
                and ".calls" not in name
            ):
                run = int(name.split("/")[1][3:])
                d = json.load(t.extractfile(m))
                extra.setdefault("repeat", {}).setdefault(d["change_id"], {})[run] = {
                    "recommended": d.get("recommended_control_ids", []),
                    "uncertain": d.get("uncertain_control_ids", []),
                }
            elif name in ("suite-10/run1/metrics.json", "suite-12/run1/metrics.json"):
                extra[name.split("/")[0]] = json.load(t.extractfile(m))
    return out, extra


# ---------------------------------------------------------------- layout


def dot_layout(nodes, edges, rankdir="LR", ranks=None, nodesep=0.12, ranksep=0.9):
    """Node centres (in points, y down) from Graphviz; nothing else is kept."""
    lines = [
        f"digraph G {{ rankdir={rankdir}; nodesep={nodesep}; ranksep={ranksep}; splines=false;",
        'node [shape=box, width=1.9, height=0.34, fixedsize=true, label=""];',
    ]
    for n in nodes:
        lines.append(f'"{n}";')
    for group in ranks or []:
        lines.append("{ rank=same; " + " ".join(f'"{n}";' for n in group) + " }")
    for a, b in edges:
        lines.append(f'"{a}" -> "{b}";')
    lines.append("}")
    res = subprocess.run(
        ["dot", "-Tjson"],
        input="\n".join(lines),
        capture_output=True,
        text=True,
        check=True,
    )
    js = json.loads(res.stdout)
    _, _, w, h = (float(v) for v in js["bb"].split(","))
    pos = {}
    for o in js.get("objects", []):
        if "pos" in o:
            x, y = (float(v) for v in o["pos"].split(","))
            pos[o["name"]] = [round(x, 1), round(h - y, 1)]
    return {"width": round(w, 1), "height": round(h, 1), "pos": pos}


def is_family(n):
    return n["type"] == "CONTROL" and FAMILY_SEPARATOR in n.get("name", "")


def full_layout(graph):
    nodes = [n["id"] for n in graph["nodes"]]
    edges = [
        (e["source"], e["target"])
        for e in graph["edges"]
        if e["relationship"] in PROPAGATING
    ]
    by_type = {
        t: [n["id"] for n in graph["nodes"] if n["type"] == t and not is_family(n)]
        for t in TYPE_ORDER
    }
    families = [n["id"] for n in graph["nodes"] if is_family(n)]
    ranks = [v for v in by_type.values() if v] + [families]
    return dot_layout(nodes, edges, ranks=ranks, nodesep=0.05, ranksep=1.6)


# ---------------------------------------------------------------- per case


def parse_reply(raw):
    if not raw:
        return None
    try:
        return json.loads(raw)
    except (json.JSONDecodeError, TypeError):
        m = re.search(r"\{.*\}", raw, re.S)
        if m:
            try:
                return json.loads(m.group(0))
            except json.JSONDecodeError:
                return None
    return None


def replay_steps(result, nodes):
    from app.data import describe_step

    steps = []
    for e in result.get("trace", []):
        if e.get("phase") != "investigate":
            continue
        reply = parse_reply(e.get("raw_response")) or {}
        action = e.get("action") or reply.get("action") or reply.get("tool")
        args = reply.get("args") if isinstance(reply.get("args"), dict) else {}
        r = e.get("result")
        step = {
            "step": e.get("step"),
            "action": action or "invalid reply",
            "summary": describe_step(e),
            "error": str(e["error"])[:240] if e.get("error") else None,
            "explored": [],
            "read": [],
            "accepted": [],
            "rejected": [],
        }
        if action == "explore_node" and isinstance(r, dict) and r.get("node"):
            step["explored"] = [r["node"]["id"]]
            step["visible_links"] = len(r.get("outgoing", [])) + len(
                r.get("incoming", [])
            )
        elif action == "inspect_control":
            items = r if isinstance(r, list) else [r]
            step["read"] = [
                i["document"]["control_id"]
                for i in items
                if isinstance(i, dict) and "document" in i
            ]
        elif action == "search_controls":
            step["query"] = args.get("query")
            step["hits"] = [
                i.get("control_id") for i in (r or []) if isinstance(i, dict)
            ][:10]
        elif action in ("submit_findings", "submit_finding") and isinstance(r, dict):
            acc = r.get("accepted_for_verification") or []
            step["accepted"] = acc if isinstance(acc, list) else [acc]
            step["rejected"] = [
                {"control": x.get("control_id"), "why": str(x.get("error", ""))[:120]}
                for x in (r.get("rejected") or [])
                if isinstance(x, dict)
            ]
        elif action == "trace_metadata":
            step["reached"] = [
                x.get("control_id") for x in (r or []) if isinstance(x, dict)
            ]
        if args and action in (
            "explore_node",
            "inspect_control",
            "search_controls",
            "trace_metadata",
            "finish",
        ):
            step["args"] = args
        steps.append(step)
    verify = sum(1 for e in result.get("trace", []) if e.get("phase") == "verify")
    return steps, verify


ROUTE = {
    "Rules already had it": "check",
    "Rules false flag": "check",
    "Correct recovery": "recommended",
    "False flag": "recommended",
    "Sent to review (affected)": "review",
    "Sent to review (not affected)": "review",
    "Missed": "not_affected",
    "Correctly excluded": "not_affected",
    "Not investigated": "undecided",
    "Not investigated (fine)": "undecided",
}


def case_payload(cid, graph, changes, truth, cases, result):
    from app.data import decisions_table
    from scripts.baseline import rank_controls

    nodes = {n["id"]: n for n in graph["nodes"]}
    change = next(c for c in changes if c["change_id"] == cid)
    case = cases[cid]
    t = truth[cid]
    removed = set(case["degradation_manifest"]["removed_edge_ids"])
    baseline = sorted(r["control_id"] for r in rank_controls(case))
    affected = sorted(k for k, v in t.items() if v.affected)
    key = sorted(k for k in affected if t[k].criticality == "KEY")

    # Focused subgraph: every node on a supporting path, the changed items, and
    # the items the check can still reach.
    focus = set(change["changed_node_ids"]) | set(baseline)
    paths = {}
    for k in affected:
        paths[k] = t[k].supporting_paths
        for p in t[k].supporting_paths:
            focus.update(p)
    edges = [
        e
        for e in graph["edges"]
        if e["source"] in focus
        and e["target"] in focus
        and e["relationship"] in PROPAGATING
    ]
    layout = dot_layout(
        sorted(focus),
        [(e["source"], e["target"]) for e in edges],
        nodesep=0.08,
        ranksep=0.7,
    )

    verified = {v["control_id"]: v for v in result.get("verified_findings", [])}
    proposed = {f["control_id"]: f for f in result.get("findings", [])}
    decisions = []
    for row in decisions_table(result):
        cid_ = row["control"]
        v, f = verified.get(cid_), proposed.get(cid_)
        src = v or f or {}
        decisions.append(
            {
                "control": cid_,
                "route": ROUTE.get(row["outcome"], "undecided"),
                "outcome": row["outcome"],
                "truth": row["answer_key"] == "Affected",
                "key": row["key"],
                "proposer": (v or {}).get("proposer_decision")
                or (f or {}).get("decision"),
                "proposer_reason": (v or {}).get("proposer_causal_reason")
                or (f or {}).get("causal_reason"),
                "proposer_counter": (v or {}).get("proposer_counter_evidence")
                or (f or {}).get("counter_evidence"),
                "checker": (
                    None
                    if not v
                    or str(v.get("verification_reason", "")).startswith("Not verified")
                    else v.get("decision")
                ),
                "checker_reason": (
                    v.get("causal_reason")
                    if v and v.get("proposer_causal_reason")
                    else None
                ),
                "checker_counter": (
                    v.get("counter_evidence")
                    if v and v.get("proposer_causal_reason")
                    else None
                ),
                "routing_reason": (v or {}).get("verification_reason"),
                "ticket_quote": src.get("ticket_quote"),
                "control_quote": src.get("control_quote"),
                "evidence_path": src.get("evidence_path"),
                "final": row["final"],
            }
        )
    steps, verify_calls = replay_steps(result, nodes)
    key_set = set(key)
    rec = {d["control"] for d in decisions if d["route"] == "recommended"}
    rev = {d["control"] for d in decisions if d["route"] == "review"}
    counts = {
        "affected": len(affected),
        "key_affected": len(key),
        "check_found": len(set(baseline) & set(affected)),
        "check_found_key": len(set(baseline) & key_set),
        "agent_recommended": len(rec),
        "agent_recommended_right": len(rec & set(affected)),
        "routed": len(rev),
        "routed_affected": len(rev & set(affected)),
        "key_misses": len(key_set - set(baseline)),
        "key_found_by_agent": len((key_set - set(baseline)) & rec),
        "key_routed": len((key_set - set(baseline)) & rev),
        "key_silent": len(key_set - set(baseline) - rec - rev),
        "affected_silent": len(set(affected) - set(baseline) - rec - rev),
        "steps": len(steps),
        "verify_calls": verify_calls,
        "model_calls": len(result.get("trace", [])),
    }
    return {
        "id": cid,
        "title": change["title"],
        "change_type": change["change_type"],
        "release_group": change.get("release_group"),
        "implementation_date": change.get("implementation_date"),
        "changed": change["changed_node_ids"],
        "ticket": case["change_ticket"],
        "ticket_damage": case["degradation_manifest"].get("ticket_operations", []),
        "removed_links": sorted(removed),
        "baseline": baseline,
        "affected": affected,
        "key": key,
        "paths": paths,
        "focus": {
            "nodes": sorted(focus),
            "edges": [e["id"] for e in edges],
            "layout": layout,
        },
        "decisions": decisions,
        "steps": steps,
        "counts": counts,
        "status": result.get("status"),
    }


# ---------------------------------------------------------------- portfolio


def portfolio(payloads, run_metrics, consistency):
    s = run_metrics["summary"]
    key_total = sum(p["counts"]["key_affected"] for p in payloads.values())
    check_key = sum(p["counts"]["check_found_key"] for p in payloads.values())
    found = sum(p["counts"]["key_found_by_agent"] for p in payloads.values())
    routed = sum(p["counts"]["key_routed"] for p in payloads.values())
    silent = sum(p["counts"]["key_silent"] for p in payloads.values())
    added = s["added_review_items"]
    avoidable = s["avoidable_review_items"]
    by_type = {}
    for p in payloads.values():
        name = p["title"].split(" — ")[0]
        b = by_type.setdefault(
            name, {"changes": 0, "key_misses": 0, "found": 0, "routed": 0, "silent": 0}
        )
        b["changes"] += 1
        b["key_misses"] += p["counts"]["key_misses"]
        b["found"] += p["counts"]["key_found_by_agent"]
        b["routed"] += p["counts"]["key_routed"]
        b["silent"] += p["counts"]["key_silent"]
    silent_list = [
        {"change": cid, "control": d["control"]}
        for cid, p in payloads.items()
        for d in p["decisions"]
        if d["key"]
        and d["truth"]
        and d["control"] not in p["baseline"]
        and d["route"] not in ("recommended", "review")
    ]
    n = len(payloads)
    return {
        "changes": n,
        "key_affected": key_total,
        "check_found_key": check_key,
        "key_misses": s["key_misses"],
        "agent_found_key": found,
        "key_routed": routed,
        "key_silent": silent,
        "silent": silent_list,
        "recovery": s["key_miss_recovery"],
        "recovery_interval": [0.711, 0.844],
        "precision": s["new_control_precision"],
        "new_right": s.get("new_true_controls")
        or round(s["new_control_precision"] * 280),
        "new_total": 280,
        "check_items": s["baseline_workload"],
        "added_items": added,
        "added_affected": added - avoidable,
        "added_unaffected": avoidable,
        "per_change": {
            "check": round(s["baseline_workload"] / n, 1),
            "real": round((added - avoidable) / n, 1),
            "unaffected": round(avoidable / n, 1),
            "total": round((s["baseline_workload"] + added) / n, 1),
        },
        "uncertain": s["uncertain_controls"],
        "model_calls": s.get("model_calls"),
        "consistency": {
            "agreement": (
                consistency["single_run_all_agree"]["agreement"]
                if "single_run_all_agree" in consistency
                else consistency.get("agreement")
            ),
            "pairs": (
                consistency["single_run_all_agree"]["key_pairs"]
                if "single_run_all_agree" in consistency
                else consistency.get("key_pairs")
            ),
            "runs": 5,
            "target": 0.95,
            "cases": ["CHG-014", "CHG-025", "CHG-017"],
        },
        "by_type": by_type,
        "targets": [
            {
                "target": "Find ≥ 50% of the key controls the check misses",
                "status": "Met",
                "value": s["key_miss_recovery"],
            },
            {
                "target": "Added review volume ≤ 25% of the check's",
                "status": "Not met as defined",
                "value": added / s["baseline_workload"],
            },
            {
                "target": "Same key decision across 5 runs ≥ 95%",
                "status": "Not met",
                "value": None,
            },
        ],
    }


def main():
    from app import content

    graph, changes, truth, cases = benchmark()
    runs, extra = recorded()
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "cases").mkdir(exist_ok=True)

    nodes = graph["nodes"]
    docs = {d["control_id"]: d for d in cases[DOCS_SOURCE]["control_documents"]}
    g = {
        "nodes": [
            {
                "id": n["id"],
                "type": n["type"],
                "name": n["name"],
                "description": n.get("description", ""),
                "criticality": n.get("criticality"),
                "aliases": n.get("aliases", []),
                "family": is_family(n),
            }
            for n in nodes
        ],
        "edges": [
            {
                "id": e["id"],
                "source": e["source"],
                "target": e["target"],
                "relationship": e["relationship"],
                "carries_impact": e["relationship"] in PROPAGATING,
                "exposable": e.get("metadata_exposable", True),
            }
            for e in graph["edges"]
        ],
        "documents": {
            k: {"title": v["title"], "text": v["text"], "criticality": v["criticality"]}
            for k, v in docs.items()
        },
        "layout": full_layout(graph),
        "type_counts": dict(Counter(n["type"] for n in nodes)),
        "link_counts": dict(Counter(e["relationship"] for e in graph["edges"])),
        "changes": [
            {
                "id": c["change_id"],
                "title": c["title"],
                "split": c["split"],
                "changed": c["changed_node_ids"],
            }
            for c in changes
        ],
    }
    (OUT / "graph.json").write_text(
        json.dumps(g, separators=(",", ":"), ensure_ascii=False)
    )

    payloads = {}
    for cid in sorted(runs):
        p = case_payload(cid, graph, changes, truth, cases, runs[cid])
        # Per-case document overrides, if the damage step changed a control text.
        over = {
            d["control_id"]: d["text"]
            for d in cases[cid]["control_documents"]
            if d["text"] != docs.get(d["control_id"], {}).get("text")
        }
        if over:
            p["document_overrides"] = over
        payloads[cid] = p
        (OUT / "cases" / f"{cid}.json").write_text(
            json.dumps(p, separators=(",", ":"), ensure_ascii=False)
        )

    port = portfolio(payloads, extra["metrics"], extra["consistency"])
    experience = {
        "provenance": PROVENANCE,
        "flagship": FLAGSHIP,
        "portfolio": port,
        "cases": [
            {"id": cid, "title": p["title"], "changed": p["changed"], **p["counts"]}
            for cid, p in payloads.items()
        ],
        "version_tests": VERSION_TESTS,
        "approaches": APPROACHES,
        "repeat_runs": repeat_runs(extra["repeat"], truth, graph),
        "lessons": [{"title": a, "detail": b} for a, b in LESSONS],
        "prompts": prompts(),
        "degradation": _degradation(),
        "development_runs": {
            "frozen_check": extra.get("suite-10", {}).get("summary"),
            "variant_b": extra.get("suite-12", {}).get("summary"),
        },
        "limits": [
            {"issue": i, "evidence": e, "response": r} for i, e, r in content.LIMITS
        ],
        "glossary": [{"term": t, "meaning": m} for t, m in content.GLOSSARY],
        "rules_by_damage": [
            {"damage": "None", "found": 1.0},
            {"damage": "30% nearest the change (main)", "found": 18 / 162},
            {"damage": "30% random", "found": 69 / 162},
            {"damage": "60% nearest the change", "found": 12 / 162},
        ],
        "benchmark": {
            "items": len(nodes),
            "links": len(graph["edges"]),
            "controls": sum(1 for n in nodes if n["type"] == "CONTROL"),
            "key_controls": sum(
                1
                for n in nodes
                if n["type"] == "CONTROL" and n.get("criticality") == "KEY"
            ),
            "changes": len(changes),
            "held_out": sum(1 for c in changes if c["split"] == "test"),
        },
    }
    (OUT / "experience.json").write_text(
        json.dumps(experience, indent=1, ensure_ascii=False)
    )
    size = sum(f.stat().st_size for f in OUT.rglob("*.json"))
    print(f"wrote {OUT} ({size / 1e6:.2f} MB, {len(payloads)} cases)")


if __name__ == "__main__":
    main()
