"""Copy compact versions of the main runs into app/recorded/ for the dashboard.

    python -m scripts.bundle_app_results <extracted detective_runs folder>

The app reads live run files from the results volume. When those are not
readable (another workspace, local development), it falls back to this
bundle, so every chart and table still shows the recorded results. Each case
file keeps the decisions in full and the investigation steps in one line each;
model replies are dropped. Labels are not stored: the app computes them.
"""

from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path

from app.data import RUN_CATALOG, describe_step

OUT = Path(__file__).resolve().parents[1] / "app" / "recorded"
KEEP = (
    "change_id",
    "status",
    "variant",
    "baseline",
    "findings",
    "verified_findings",
    "recommended_control_ids",
    "uncertain_control_ids",
    "uninvestigated_control_ids",
    "coverage",
)


def compact_case(result: dict) -> dict:
    out = {k: result[k] for k in KEEP if k in result}
    out["trace"] = [
        {
            "phase": "investigate",
            "step": e.get("step"),
            "action": e.get("action"),
            "error": str(e["error"])[:300] if e.get("error") else None,
            "what": describe_step(e),
        }
        for e in result.get("trace", [])
        if e.get("phase") == "investigate"
    ]
    out["model_calls"] = len(result.get("trace", []))
    return out


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("source")
    args = p.parse_args()
    src = Path(args.source)
    if OUT.exists():
        shutil.rmtree(OUT)
    for entry in RUN_CATALOG:
        folder = src / entry["folder"]
        if not folder.is_dir():
            print("missing", folder)
            continue
        for extra in ("consistency.json",):
            if (folder / extra).exists():
                (OUT / entry["folder"]).mkdir(parents=True, exist_ok=True)
                shutil.copy(folder / extra, OUT / entry["folder"] / extra)
        for run in sorted(folder.glob("run*")):
            dst = OUT / entry["folder"] / run.name
            dst.mkdir(parents=True, exist_ok=True)
            if (run / "metrics.json").exists():
                shutil.copy(run / "metrics.json", dst / "metrics.json")
            for f in sorted(run.glob("CHG-*.json")):
                if ".calls" in f.name:
                    continue
                r = json.loads(f.read_text())
                if "coverage" not in r:
                    continue
                (dst / f.name).write_text(json.dumps(compact_case(r)) + "\n")
    size = sum(f.stat().st_size for f in OUT.rglob("*") if f.is_file())
    print(f"wrote {OUT} ({size / 1e6:.1f} MB)")


if __name__ == "__main__":
    main()
