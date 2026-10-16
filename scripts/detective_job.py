"""Run the detective suite as a Databricks job, so it survives closed terminals.

Submit (prints a run ID and a link):

    python -m scripts.detective_job submit --change-ids CHG-014 CHG-025 CHG-017 \
        --output-dir /Volumes/workspace/default/detective_runs/suite-09

List recent runs (to find a lost run ID):

    python -m scripts.detective_job list

Check status and the job's printed output:

    python -m scripts.detective_job status <run_id>

The job always passes --resume, so resubmitting continues where the last run
stopped. It runs on serverless compute with the workspace's own credentials.
"""

import argparse
import json
import os
import time

DEFAULT_REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _client():
    from databricks.sdk import WorkspaceClient

    return WorkspaceClient()


def build_body(repo, args):
    """repo is the /Workspace/... path; python_file uses the workspace path without it."""
    ws_path = repo[len("/Workspace") :] if repo.startswith("/Workspace/") else repo
    params = [
        repo,
        "--model",
        args.model,
        "--max-steps",
        str(args.max_steps),
        "--output-dir",
        args.output_dir,
        "--resume",
    ]
    if args.change_ids:
        params += ["--change-ids", *args.change_ids]
    if args.max_cases is not None:
        params += ["--max-cases", str(args.max_cases)]
    if args.runs != 1:
        params += ["--runs", str(args.runs)]
    if getattr(args, "variant", None):
        params += ["--variant", args.variant]
    if getattr(args, "split", "development") != "development":
        params += [
            "--split",
            args.split,
            "--confirm-heldout",
            args.confirm_heldout or "",
        ]
    if getattr(args, "run_index", 1) != 1:
        params += ["--run-index", str(args.run_index)]
    if getattr(args, "seed", None) is not None:
        params += ["--seed", str(args.seed)]
    if getattr(args, "level", None) is not None:
        params += ["--level", str(args.level)]
    if getattr(args, "mode", None):
        params += ["--mode", args.mode]
    if getattr(args, "ignore_lock", False):
        params += ["--ignore-lock"]
    return {
        "run_name": "detective-suite "
        + os.path.basename(args.output_dir.rstrip("/"))
        + (f" variant {args.variant}" if getattr(args, "variant", None) else "")
        + (
            f" run{args.run_index}"
            if getattr(args, "run_index", 1) != 1 or getattr(args, "runs", 1) != 1
            else ""
        ),
        "timeout_seconds": 0,
        "tasks": [
            {
                "task_key": "detective",
                "environment_key": "default",
                "spark_python_task": {
                    "python_file": ws_path + "/scripts/job_entry.py",
                    "parameters": params,
                    "source": "WORKSPACE",
                },
            }
        ],
        "environments": [
            {
                "environment_key": "default",
                "spec": {"client": "2", "dependencies": ["databricks-sdk>=0.30,<1"]},
            }
        ],
    }


def submit(args):
    repo = args.repo
    if not repo.startswith("/Workspace/"):
        raise SystemExit(
            f"--repo must be the workspace path of the repository, got {repo!r}. "
            "Run this from the repository folder under /Workspace, or pass --repo."
        )
    w = _client()
    body = build_body(repo.rstrip("/"), args)
    out = w.api_client.do("POST", "/api/2.2/jobs/runs/submit", body=body)
    run_id = out["run_id"]
    print(f"submitted run_id={run_id}")
    print(f"link: {w.config.host.rstrip('/')}/jobs/runs/{run_id}")
    print(f"status: python -m scripts.detective_job status {run_id}")


def status(args):
    w = _client()
    run = w.api_client.do(
        "GET", "/api/2.2/jobs/runs/get", query={"run_id": args.run_id}
    )
    state = run.get("status") or run.get("state", {})
    print("state:", json.dumps(state))
    for task in run.get("tasks", []):
        try:
            out = w.api_client.do(
                "GET", "/api/2.2/jobs/runs/get-output", query={"run_id": task["run_id"]}
            )
        except Exception as exc:  # output not ready yet
            print("output not available yet:", str(exc)[:120])
            continue
        if out.get("error"):
            print("error:", out["error"])
            print((out.get("error_trace") or "")[-2000:])
        logs = out.get("logs") or ""
        print(logs[-args.tail :] if logs else "(no output yet)")


def list_runs(args):
    """Recent one-time runs, newest first, so a lost run ID can be recovered."""
    w = _client()
    out = w.api_client.do(
        "GET",
        "/api/2.2/jobs/runs/list",
        query={"run_type": "SUBMIT_RUN", "limit": args.limit},
    )
    import datetime as _dt

    for run in out.get("runs", []):
        state = run.get("status", {}).get("state") or run.get("state", {}).get(
            "life_cycle_state"
        )
        started = run.get("start_time")
        when = (
            _dt.datetime.fromtimestamp(started / 1000).strftime("%Y-%m-%d %H:%M")
            if started
            else "-"
        )
        print(f"{run['run_id']}  {when}  {state:<12}  {run.get('run_name', '')}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("submit")
    s.add_argument(
        "--repo",
        default=DEFAULT_REPO,
        help="Workspace path of the repository, e.g. /Workspace/Users/<you>/payments-control-impact",
    )
    s.add_argument("--model", default="databricks-gpt-oss-120b")
    s.add_argument("--change-ids", nargs="*")
    s.add_argument("--max-cases", type=int)
    s.add_argument("--max-steps", type=int, default=60)
    s.add_argument("--runs", type=int, default=1)
    s.add_argument("--output-dir", required=True)
    s.add_argument("--ignore-lock", action="store_true")
    s.add_argument("--split", choices=["development", "test"], default="development")
    s.add_argument("--confirm-heldout")
    s.add_argument("--variant", choices=["A", "B", "C"])
    s.add_argument("--run-index", type=int, default=1)
    s.add_argument("--seed", type=int)
    s.add_argument("--level", type=int, choices=[0, 30, 60])
    s.add_argument("--mode", choices=["random", "correlated"])
    s.set_defaults(func=submit)
    t = sub.add_parser("status")
    t.add_argument("run_id", type=int)
    t.add_argument("--tail", type=int, default=3000)
    t.set_defaults(func=status)
    lst = sub.add_parser("list")
    lst.add_argument("--limit", type=int, default=10)
    lst.set_defaults(func=list_runs)
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
