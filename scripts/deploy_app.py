"""Deploy the Control Impact Detective Databricks App.

    python -m scripts.deploy_app            # upload, create or update, grant, deploy
    python -m scripts.deploy_app --status   # show the app's URL and state

Run from a copy of the repository in a Databricks terminal (workspace
authentication). Steps, each idempotent:
1. Upload the app bundle (app/, scripts/, docs, benchmark data) to
   /Workspace/Users/<you>/apps/<name> through the Workspace API.
2. Create the app if missing, with the model endpoint as a resource (CAN_QUERY).
3. Wait for its compute, grant its service principal read access to the
   results volume (USE CATALOG, USE SCHEMA, READ VOLUME).
4. Deploy the bundle and wait for the deployment to finish.
"""

from __future__ import annotations

import argparse
import base64
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BUNDLE = [
    ("app/app.py", "app/app.py"),
    ("app/__init__.py", "app/__init__.py"),
    ("app/content.py", "app/content.py"),
    ("app/data.py", "app/data.py"),
    ("app/qa.py", "app/qa.py"),
    ("app/app.yaml", "app.yaml"),
    ("app/requirements.txt", "requirements.txt"),
    ("README.md", "README.md"),
    ("data/README.md", "data/README.md"),
]
BUNDLE_GLOBS = ["scripts/*.py", "docs/*.md", "data/ground_truth/*.json"]


def bundle_files():
    files = list(BUNDLE)
    for pattern in BUNDLE_GLOBS:
        for p in sorted(ROOT.glob(pattern)):
            rel = p.relative_to(ROOT).as_posix()
            files.append((rel, rel))
    return files


def _client():
    from databricks.sdk import WorkspaceClient

    return WorkspaceClient()


def _do(w, method, path, body=None, query=None):
    return w.api_client.do(method, path, body=body, query=query)


def _exists(w, name):
    try:
        return _do(w, "GET", f"/api/2.0/apps/{name}")
    except Exception as exc:
        if "does not exist" in str(exc) or "NOT_FOUND" in str(exc) or "404" in str(exc):
            return None
        raise


def upload(w, dest):
    _do(w, "POST", "/api/2.0/workspace/mkdirs", {"path": dest})
    made = {dest}
    for src, rel in bundle_files():
        target = f"{dest}/{rel}"
        parent = target.rsplit("/", 1)[0]
        if parent not in made:
            _do(w, "POST", "/api/2.0/workspace/mkdirs", {"path": parent})
            made.add(parent)
        content = base64.b64encode((ROOT / src).read_bytes()).decode()
        _do(
            w,
            "POST",
            "/api/2.0/workspace/import",
            {"path": target, "format": "AUTO", "content": content, "overwrite": True},
        )
    print(f"uploaded {len(bundle_files())} files to {dest}")


def wait_for(w, name, field, good, bad=("ERROR", "FAILED"), timeout=900):
    start = time.time()
    while time.time() - start < timeout:
        app = _do(w, "GET", f"/api/2.0/apps/{name}")
        state = (app.get(field) or {}).get("state")
        if state in good:
            return app
        if state in bad:
            raise SystemExit(
                f"{field} is {state}: {(app.get(field) or {}).get('message')}"
            )
        print(f"  waiting: {field} = {state}", flush=True)
        time.sleep(15)
    raise SystemExit(f"timed out waiting for {field}")


def grant(w, sp, catalog, schema, volume):
    for kind, full, priv in (
        ("catalog", catalog, "USE_CATALOG"),
        ("schema", f"{catalog}.{schema}", "USE_SCHEMA"),
        ("volume", f"{catalog}.{schema}.{volume}", "READ_VOLUME"),
    ):
        try:
            _do(
                w,
                "PATCH",
                f"/api/2.1/unity-catalog/permissions/{kind}/{full}",
                {"changes": [{"principal": sp, "add": [priv]}]},
            )
            print(f"granted {priv} on {kind} {full}")
        except Exception as exc:
            print(f"WARNING: could not grant {priv} on {full}: {str(exc)[:160]}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--name", default="control-impact-detective")
    parser.add_argument("--endpoint", default="databricks-gpt-oss-120b")
    parser.add_argument("--catalog", default="workspace")
    parser.add_argument("--schema", default="default")
    parser.add_argument("--volume", default="detective_runs")
    parser.add_argument("--status", action="store_true")
    args = parser.parse_args()
    w = _client()

    if args.status:
        app = _exists(w, args.name)
        if not app:
            raise SystemExit(f"app {args.name} does not exist yet")
        print("url:", app.get("url"))
        print("compute:", (app.get("compute_status") or {}).get("state"))
        print(
            "app:",
            (app.get("app_status") or {}).get("state"),
            (app.get("app_status") or {}).get("message", ""),
        )
        dep = app.get("active_deployment") or app.get("pending_deployment") or {}
        print(
            "deployment:",
            (dep.get("status") or {}).get("state"),
            (dep.get("status") or {}).get("message", ""),
        )
        src = dep.get("source_code_path")
        if src:
            for rel in ("app.yaml", "requirements.txt", "app/app.py", "app/data.py"):
                try:
                    info = _do(
                        w,
                        "GET",
                        "/api/2.0/workspace/get-status",
                        query={"path": f"{src}/{rel}"},
                    )
                    print(f"  {rel}: {info.get('object_type')}")
                except Exception as exc:
                    print(f"  {rel}: MISSING ({str(exc)[:80]})")
        return

    me = _do(w, "GET", "/api/2.0/preview/scim/v2/Me")["userName"]
    dest = f"/Workspace/Users/{me}/apps/{args.name}"
    upload(w, dest)

    app = _exists(w, args.name)
    if app is None:
        print(f"creating app {args.name}")
        _do(
            w,
            "POST",
            "/api/2.0/apps",
            {
                "name": args.name,
                "description": "Control Impact Detective: results and evidence for the payments control-impact POC",
                "resources": [
                    {
                        "name": "llm-endpoint",
                        "description": "Model used by the Ask a question page",
                        "serving_endpoint": {
                            "name": args.endpoint,
                            "permission": "CAN_QUERY",
                        },
                    }
                ],
            },
        )
    app = _do(w, "GET", f"/api/2.0/apps/{args.name}")
    if (app.get("compute_status") or {}).get("state") in ("STOPPED", "STOPPING"):
        print("starting app compute")
        _do(w, "POST", f"/api/2.0/apps/{args.name}/start")
    app = wait_for(w, args.name, "compute_status", good=("ACTIVE",))

    sp = app.get("service_principal_client_id")
    if sp:
        grant(w, sp, args.catalog, args.schema, args.volume)
    else:
        print("WARNING: app has no service principal id yet; volume access not granted")

    print("deploying")
    dep = _do(
        w,
        "POST",
        f"/api/2.0/apps/{args.name}/deployments",
        {"source_code_path": dest, "mode": "SNAPSHOT"},
    )
    dep_id = dep.get("deployment_id")
    start = time.time()
    while time.time() - start < 900:
        d = _do(w, "GET", f"/api/2.0/apps/{args.name}/deployments/{dep_id}")
        state = (d.get("status") or {}).get("state")
        if state == "SUCCEEDED":
            break
        if state in ("FAILED", "CANCELLED"):
            raise SystemExit(
                f"deployment {state}: {(d.get('status') or {}).get('message')}"
            )
        print(f"  waiting: deployment = {state}", flush=True)
        time.sleep(15)
    app = _do(w, "GET", f"/api/2.0/apps/{args.name}")
    print("deployed. Open:", app.get("url"))


if __name__ == "__main__":
    main()
