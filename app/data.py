"""Load run results and the answer key for the app.

Results live in a Unity Catalog volume (RESULTS_ROOT, default
/Volumes/workspace/default/detective_runs). Inside a Databricks App the volume
is read through the Files API; locally (tests, development) RESULTS_ROOT can be
an ordinary folder. Labels are computed from the benchmark code here, offline;
nothing in this module is sent to a model.
"""

from __future__ import annotations

import json
import os
from functools import lru_cache
from pathlib import Path

RESULTS_ROOT = os.environ.get(
    "RESULTS_ROOT", "/Volumes/workspace/default/detective_runs"
)

# Runs the app knows how to describe. Each entry: folder, label, what it is.
RUN_CATALOG = [
    {
        "folder": "heldout-final",
        "label": "Held-out test (18 cases)",
        "kind": "heldout",
        "about": "The final evaluation: all 18 test-split cases, one run, chosen variant, everything frozen.",
    },
    {
        "folder": "suite-10",
        "label": "Frozen check, variant A (8 unseen cases)",
        "kind": "frozen",
        "about": "Eight development cases whose change types were never inspected during fixing; code frozen at 799189a.",
    },
    {
        "folder": "suite-12",
        "label": "A/B test, variant B (same 8 cases)",
        "kind": "ab",
        "about": "Variant B requires a cited chain for AFFECTED findings; compared with variant A by a pre-registered rule.",
    },
    {
        "folder": "suite-11",
        "label": "Consistency (3 cases x 5 runs)",
        "kind": "consistency",
        "about": "CHG-014, CHG-025 and CHG-017 run five times to measure run-to-run agreement on key controls.",
    },
]

# Results produced in an earlier workspace (raw files not in this volume).
EARLIER_RESULTS = {
    "tuned": {
        "label": "Tuned development cases (4)",
        "cases": [
            # change, title, key misses, recovered, new true, new false, uncertain
            ("CHG-001", "Debtor town-name mapping", 19, 14, 30, 5, 19),
            ("CHG-014", "Authorization exception report", 0, 0, 4, 0, 0),
            ("CHG-025", "Outbound message mapping", 3, 3, 4, 0, 20),
            ("CHG-017", "Settlement-status feed", 5, 5, 18, 0, 2),
        ],
    },
    "before_after": {
        "case": "CHG-001",
        "before": {"recovered": 0, "misses": 19, "failed_steps": 56, "steps": 60},
        "after": {"recovered": 14, "misses": 19, "failed_steps": 0, "steps": 59},
    },
    "phases": [
        ("Phase 1: hybrid ranking", "36 dev cases, 5 runs", 49.5),
        ("Phase 2: edge proposals", "18 held-out cases", 57.6),
    ],
}


# ---------------------------------------------------------------- storage


def _is_volume(path: str) -> bool:
    return path.startswith("/Volumes/")


@lru_cache(maxsize=1)
def _client():
    from databricks.sdk import WorkspaceClient

    return WorkspaceClient()


def _local_path(path: str) -> Path | None:
    p = Path(path)
    return p if p.exists() else None


def read_text(path: str) -> str | None:
    """Read a file from the volume (Files API) or the local disk; None if absent."""
    local = _local_path(path)
    if local is not None and local.is_file():
        return local.read_text(encoding="utf-8")
    if _is_volume(path):
        try:
            resp = _client().files.download(path)
            return resp.contents.read().decode("utf-8")
        except Exception:
            return None
    return None


def list_names(path: str) -> list[str]:
    """Names in a directory, from the volume or local disk; [] if absent."""
    local = _local_path(path)
    if local is not None and local.is_dir():
        return sorted(p.name for p in local.iterdir())
    if _is_volume(path):
        try:
            return sorted(
                e.name or Path(e.path).name
                for e in _client().files.list_directory_contents(path)
            )
        except Exception:
            return []
    return []


def read_json(path: str):
    text = read_text(path)
    if text is None:
        return None
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return None


# ---------------------------------------------------------------- runs


def run_dirs(folder: str) -> list[str]:
    base = f"{RESULTS_ROOT}/{folder}"
    return [n for n in list_names(base) if n.startswith("run")]


def run_metrics(folder: str, run: str = "run1"):
    return read_json(f"{RESULTS_ROOT}/{folder}/{run}/metrics.json")


def case_ids(folder: str, run: str = "run1") -> list[str]:
    names = list_names(f"{RESULTS_ROOT}/{folder}/{run}")
    return sorted(
        n[:-5]
        for n in names
        if n.startswith("CHG-") and n.endswith(".json") and ".calls" not in n
    )


def case_result(folder: str, run: str, change_id: str):
    return read_json(f"{RESULTS_ROOT}/{folder}/{run}/{change_id}.json")


def consistency(folder: str = "suite-11"):
    return read_json(f"{RESULTS_ROOT}/{folder}/consistency.json")


def available_runs() -> list[dict]:
    """Catalog entries whose folder holds at least one finished run summary."""
    out = []
    for entry in RUN_CATALOG:
        runs = run_dirs(entry["folder"])
        metrics = [m for m in (run_metrics(entry["folder"], r) for r in runs) if m]
        cases = case_ids(entry["folder"], runs[0]) if runs else []
        if runs or cases:
            out.append({**entry, "runs": runs, "metrics": metrics, "cases": cases})
    return out


# ---------------------------------------------------------------- answer key


@lru_cache(maxsize=1)
def answer_key():
    """Per-change labels and names from the benchmark (computed offline)."""
    from scripts.baseline import rank_controls
    from scripts.evaluate_baseline import _truth_by_change
    from scripts.generate_benchmark import build_changes, build_graph
    from scripts.generate_observable import build_condition

    graph, changes = build_graph(), build_changes()
    truth = _truth_by_change(graph, changes)
    cases = {}
    for c in build_condition(graph, changes, 30, "correlated")["cases"]:
        tr = truth[c["change_id"]]
        cases[c["change_id"]] = {
            "title": c["change_ticket"]["title"],
            "text": c["change_ticket"]["text"],
            "split": c["split"],
            "changed": c["change_ticket"]["changed_entity_ids"],
            "affected": sorted(k for k, v in tr.items() if v.affected),
            "key_affected": sorted(
                k for k, v in tr.items() if v.affected and v.criticality == "KEY"
            ),
            "baseline": sorted(r["control_id"] for r in rank_controls(c)),
            "paths": {k: v.supporting_paths[:1] for k, v in tr.items() if v.affected},
        }
    nodes = {n["id"]: n for n in graph["nodes"]}
    return {"cases": cases, "nodes": nodes}


def control_title(cid: str) -> str:
    n = answer_key()["nodes"].get(cid, {})
    return n.get("name", "")


def is_key(cid: str) -> bool:
    return answer_key()["nodes"].get(cid, {}).get("criticality") == "KEY"


def decisions_table(result: dict) -> list[dict]:
    """One row per control the agent decided or should have found, with an outcome."""
    key = answer_key()["cases"].get(result.get("change_id"), {})
    affected = set(key.get("affected", []))
    base = {b["control_id"] for b in result.get("baseline", [])}
    verified = {v["control_id"]: v for v in result.get("verified_findings", [])}
    findings = {f["control_id"]: f for f in result.get("findings", [])}
    ids = set(findings) | set(verified) | affected | base
    rows = []
    for cid in ids:
        f, v = findings.get(cid), verified.get(cid)
        final = v["decision"] if v else (f["decision"] if f else None)
        truth = cid in affected
        if cid in base:
            outcome = "Rules already had it" if truth else "Rules false flag"
        elif final == "AFFECTED":
            outcome = "Correct recovery" if truth else "False flag"
        elif final == "UNCERTAIN":
            outcome = (
                "Sent to review (affected)"
                if truth
                else "Sent to review (not affected)"
            )
        elif final == "UNAFFECTED":
            outcome = "Missed" if truth else "Correctly excluded"
        else:
            outcome = "Not investigated" if truth else "Not investigated (fine)"
        verifier = None
        if v and v.get("verification_reason") != "Not verified (proposer UNAFFECTED)":
            reason = v.get("verification_reason")
            verifier = (
                f"tie-break → {v.get('decision')}"
                if str(reason).startswith("Tie-break")
                else (
                    "disagreed"
                    if str(reason).startswith("Proposer and verifier disagree")
                    else (
                        "failed"
                        if reason == "Verification unavailable"
                        else v.get("decision")
                    )
                )
            )
        rows.append(
            {
                "control": cid,
                "title": control_title(cid),
                "key": is_key(cid),
                "agent": f["decision"] if f else ("(rules)" if cid in base else "none"),
                "verifier": verifier or "",
                "final": (
                    "(rules)" if cid in base and final != "AFFECTED" else (final or "")
                ),
                "answer_key": "Affected" if truth else "Not affected",
                "outcome": outcome,
                "agent_reason": (v or {}).get("proposer_causal_reason")
                or (f or {}).get("causal_reason", ""),
                "verifier_reason": (
                    (v or {}).get("causal_reason", "")
                    if v and v.get("proposer_causal_reason")
                    else ""
                ),
            }
        )
    order = {
        "False flag": 0,
        "Missed": 1,
        "Sent to review (affected)": 2,
        "Correct recovery": 3,
    }
    rows.sort(key=lambda r: (not r["key"], order.get(r["outcome"], 9), r["control"]))
    return rows


def step_rows(result: dict) -> list[dict]:
    """The investigation, one row per step, in plain words."""
    rows = []
    for e in result.get("trace", []):
        if e.get("phase") != "investigate":
            continue
        rows.append(
            {
                "step": e.get("step"),
                "action": e.get("action") or "invalid reply",
                "what": describe_step(e),
                "rejected": bool(e.get("error")),
            }
        )
    return rows


def describe_step(e: dict) -> str:
    a, r = e.get("action"), e.get("result")
    if e.get("error"):
        return "Rejected: " + str(e["error"])[:200]
    if a == "explore_node" and isinstance(r, dict) and r.get("node"):
        n = r["node"]
        return f"Explored {n.get('id')} ({n.get('name', '')}): {len(r.get('outgoing', []))} outgoing, {len(r.get('incoming', []))} incoming visible links"
    if a == "trace_metadata":
        return f"Ran the rules baseline: {len(r) if isinstance(r, list) else '?'} controls reachable through visible lineage"
    if a == "search_controls":
        return f"Searched control procedures: {len(r) if isinstance(r, list) else '?'} results"
    if a == "inspect_control":
        items = r if isinstance(r, list) else [r]
        ids = [
            i["document"]["control_id"]
            for i in items
            if isinstance(i, dict) and "document" in i
        ]
        return f"Read {len(ids)} control procedures: {', '.join(ids)}"
    if a in ("submit_findings", "submit_finding"):
        acc = (r or {}).get("accepted_for_verification")
        n = len(acc) if isinstance(acc, list) else (1 if acc else 0)
        rej = len((r or {}).get("rejected", []) or [])
        return f"Submitted findings: {n} accepted" + (
            f", {rej} rejected" if rej else ""
        )
    if a == "finish":
        return (
            "Tried to finish early and was reminded to continue"
            if isinstance(r, dict) and r.get("not_finished")
            else "Finished the investigation"
        )
    return str(a)
