"""Summarise a saved detective run: step errors, actions, and verifier outcomes.

python -m scripts.inspect_detective_run output/runs/detective-suite-02/run1/CHG-001.json
"""

import argparse
import collections
import json
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("result")
    parser.add_argument("--examples", type=int, default=2)
    args = parser.parse_args()
    r = json.loads(Path(args.result).read_text(encoding="utf-8"))
    steps = [e for e in r["trace"] if e.get("phase") == "investigate"]
    verify = [e for e in r["trace"] if e.get("phase") == "verify"]

    print("status:", r.get("status"), "| coverage:", r.get("coverage"))
    print("\nINVESTIGATE steps:", len(steps))
    print(
        "  errors:",
        collections.Counter(e.get("error", "OK")[:90] for e in steps).most_common(6),
    )
    print("  actions:", [e.get("action") for e in steps])

    print("\nVERIFY calls:", len(verify))
    print(
        "  errors:",
        collections.Counter(e.get("error", "OK")[:90] for e in verify).most_common(6),
    )
    outcomes = collections.Counter(
        (
            f.get("proposer_decision", "-"),
            f["decision"],
            f.get("verification_reason", ""),
        )
        for f in r.get("verified_findings", [])
    )
    print("  (proposer, final, reason):")
    for k, n in outcomes.most_common(8):
        print("   ", n, k)

    shown = 0
    for f in r.get("verified_findings", []):
        if f["decision"] != "UNCERTAIN" or shown >= args.examples:
            continue
        e = next((x for x in verify if x["control_id"] == f["control_id"]), {})
        print("\n---- UNCERTAIN", f["control_id"], "| verify error:", e.get("error"))
        print("  proposer reason:", str(f.get("causal_reason", ""))[:300])
        for raw in e.get("raw_responses", [e.get("raw_response")]):
            print("  verifier raw:", repr(raw)[:700])
        shown += 1

    bad = [e for e in steps if "error" in e][: args.examples]
    for e in bad:
        print("\n---- step", e["step"], "error:", e["error"][:150])
        print("  raw:", repr(e.get("raw_response"))[:500])


if __name__ == "__main__":
    main()
