# Payments Control Impact Explorer — Databricks App

A read-only executive explorer for **actual saved held-out POC results**. This is a Databricks-hosted Streamlit application, not a live model inference service.

## What it does
- Executive KPIs and predeclared targets.
- Selectable held-out change requests, recovered versus still-missed controls.
- Per-case breakdowns and validation caveats.
- Exploratory simulated-review results kept separate from primary POC claims.

## Deployment
Deploy from a Databricks workspace with **Databricks Apps** enabled and permission to create apps.

1. Clone/import the entire repository into your Databricks workspace (the `output/heldout_run/heldout_results.json` file is required).
2. Create a Databricks App and point its source to the repository root containing `app/app.yaml`. If your workspace requires `app.yaml` at the app source root, set the source to the repository root and copy `app/app.yaml` there, or package the app directory with its required artifacts.
3. Install `app/requirements.txt` in the app environment. Databricks Apps may expect a root-level requirements file; copy this file to the deployment source root if necessary.
4. Launch the app and confirm the 18 scenarios and headline counts.

Local smoke test from repository root:
```bash
pip install -r app/requirements.txt
streamlit run app/app.py
```

## Important limits
The saved summary artifact contains per-case control IDs and metrics, **not** enough data to construct an honest before/after dependency graph or show source evidence. Those require a case-keyed export of original/proposed edges and visible source snippets from the evaluation pipeline. This application deliberately does not fabricate them.

No live Databricks endpoint, Unity Catalog table, or secrets are required for replay mode. This is an initial executive-ready shell, not a finished production interface.
