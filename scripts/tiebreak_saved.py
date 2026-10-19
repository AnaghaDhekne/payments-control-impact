"""Apply the tie-break step to saved runs of version A, without rerunning them.

    python -m scripts.tiebreak_saved --input-dir <runs folder> --output-dir <out> \
        --runs 1 [--level 30 --mode correlated]

For every case in <input-dir>/run<N>/ the saved investigation is kept exactly
as it was. Only the controls where the proposer and verifier disagreed get one
extra model call: the same tie-break as variants C and D (scripts.detective).
The updated result goes to <output-dir>/run<N>/<case>.json, so the same run can
be scored with and without the tie-break (scripts.compare_runs), free of
run-to-run noise. Cases already written to the output are skipped (resume).
"""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

from scripts.case_io import case_digest, observable_payload
from scripts.detective import (
    EvidenceTools,
    _adjudicate,
    _object,
    verification_evidence,
)
from scripts.generate_benchmark import build_changes, build_graph
from scripts.generate_observable import SEED, build_condition

DISAGREE = "Proposer and verifier disagree"


def verifier_verdict(result, cid):
    """The verifier's own decision for a control, from its saved reply."""
    for e in result.get("trace", []):
        if e.get("phase") == "verify" and e.get("control_id") == cid:
            raws = e.get("raw_responses") or [e.get("raw_response")]
            for raw in reversed([r for r in raws if r]):
                try:
                    reply = _object(raw)
                except (ValueError, TypeError):
                    continue
                if reply.get("decision") in ("AFFECTED", "UNAFFECTED", "UNCERTAIN"):
                    return {
                        "decision": reply["decision"],
                        "causal_reason": str(reply.get("causal_reason") or ""),
                        "counter_evidence": str(
                            reply.get("counter_evidence") or "None stated."
                        ),
                    }
    return None


def apply_tiebreak(result, case, llm):
    """Return a copy of a saved result with disagreements resolved by the tie-break."""
    payload = observable_payload(case)
    if result.get("case_digest") not in (None, case_digest(payload)):
        raise ValueError(f"{result['change_id']}: saved run is for a different case")
    tools = EvidenceTools(payload)
    findings = {f["control_id"]: f for f in result.get("findings", [])}
    tools.inspected = set(findings)
    ticket = payload["change_ticket"]
    out = json.loads(json.dumps(result))
    trace = out.setdefault("trace", [])
    verified, n = [], 0
    for review in out.get("verified_findings", []):
        cid = review["control_id"]
        finding = findings.get(cid)
        verdict = verifier_verdict(result, cid)
        if review.get("verification_reason") != DISAGREE or not finding or not verdict:
            verified.append(review)
            continue
        entry = {"phase": "tiebreak", "control_id": cid}
        evidence = verification_evidence(tools, ticket, finding)
        verified.append(
            _adjudicate(llm, payload, tools, evidence, finding, verdict, entry, review)
        )
        trace.append(entry)
        n += 1
    out["verified_findings"] = verified
    baseline = {b["control_id"] for b in out["baseline"]}
    out["recommended_control_ids"] = sorted(
        baseline | {v["control_id"] for v in verified if v["decision"] == "AFFECTED"}
    )
    out["uncertain_control_ids"] = sorted(
        v["control_id"] for v in verified if v["decision"] == "UNCERTAIN"
    )
    out["tiebreak_applied"] = {"calls": n, "variant": "A + tie-break (offline)"}
    return out


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--input-dir", required=True)
    p.add_argument("--output-dir", required=True)
    p.add_argument("--runs", nargs="+", type=int, default=[1])
    p.add_argument("--level", type=int, default=30)
    p.add_argument("--mode", default="correlated")
    p.add_argument("--seed", type=int, default=SEED)
    p.add_argument("--model", default="databricks-gpt-oss-120b")
    p.add_argument("--max-tokens", type=int, default=8000)
    args = p.parse_args()

    from scripts.databricks_llm import DatabricksChatLLM

    llm = DatabricksChatLLM(args.model, max_tokens=args.max_tokens)
    cases = {
        c["change_id"]: c
        for c in build_condition(
            build_graph(), build_changes(), args.level, args.mode, args.seed
        )["cases"]
    }
    for run in args.runs:
        src = Path(args.input_dir) / f"run{run}"
        dst = Path(args.output_dir) / f"run{run}"
        dst.mkdir(parents=True, exist_ok=True)
        for f in sorted(src.glob("CHG-*.json")):
            if ".calls" in f.name:
                continue
            target = dst / f.name
            if target.exists():
                print(f"[run {run}] {f.stem} already done", flush=True)
                continue
            result = json.loads(f.read_text())
            if "coverage" not in result:
                print(f"[run {run}] {f.stem} unfinished in source; skipped", flush=True)
                continue
            started = time.time()
            out = apply_tiebreak(result, cases[result["change_id"]], llm)
            target.write_text(json.dumps(out, indent=2, default=str) + "\n")
            moved = sum(
                1
                for v in out["verified_findings"]
                if str(v.get("verification_reason", "")).startswith("Tie-break")
            )
            print(
                f"[run {run}] {f.stem}: {out['tiebreak_applied']['calls']} tie-breaks, "
                f"{moved} resolved, {round(time.time() - started)} s",
                flush=True,
            )


if __name__ == "__main__":
    main()
