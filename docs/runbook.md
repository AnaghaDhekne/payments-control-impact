# Runbook

## Offline (any machine)

```bash
python -m pip install -r requirements-dev.txt
python -m pytest -q                 # scripted model responses; no credentials
python -m black --check scripts tests
python -m scripts.validate_graph
python -m scripts.evaluate_baseline > baseline_results.json
python -m scripts.generate_benchmark   # regenerate data/ground_truth benchmark files
python -m scripts.generate_observable  # write data/observable/*.json (ignored by Git)
```

CI (`.github/workflows/ci.yml`) runs formatting, tests, graph validation and
the baseline evaluation on every push.

## Databricks setup (once)

1. Add the repository as a Git folder under `/Workspace/Users/<you>/`.
2. Make sure a chat model is listed under **Serving**. The default is
   `databricks-gpt-oss-120b`; pass another with `--model`.
3. Create a volume for results (workspace folders reject some writes from
   terminals and jobs):

   ```bash
   python -c "
   from databricks.sdk import WorkspaceClient
   from databricks.sdk.service.catalog import VolumeType
   WorkspaceClient().volumes.create(catalog_name='workspace', schema_name='default',
       name='detective_runs', volume_type=VolumeType.MANAGED)"
   ```

Authentication uses the workspace's own credentials. Never put tokens in
files or commits.

## Working copy

Imports straight from a `/Workspace` Git folder can fail right after
`git pull`. Work from a local copy:

```bash
cd /Workspace/Users/<you>/payments-control-impact && git pull -q && rm -rf /tmp/pci && cp -r . /tmp/pci && cd /tmp/pci
```

## Check the endpoint (1 minute)

```bash
python -m scripts.probe_model --n 6
```

Expect 5–6 of 6 usable. If fewer, fix the model setup before a full run.

## Run cases as a job (recommended)

Web-terminal background processes are ended when the session ends. Jobs are not.

```bash
python -m scripts.detective_job submit \
    --repo /Workspace/Users/<you>/payments-control-impact \
    --change-ids CHG-001 CHG-014 CHG-025 CHG-017 \
    --output-dir /Volumes/workspace/default/detective_runs/<run-name>
python -m scripts.detective_job status <run_id>
```

- Each case prints `key misses …, recovered …` when done; the pooled summary
  prints at the end. A case takes about 10 minutes.
- Omit `--change-ids` to run all 36 development cases; add `--runs 5` for
  consistency.
- Jobs always pass `--resume`: resubmitting with the same `--output-dir`
  continues unfinished cases and rescores finished ones.
- In the UI: **Jobs & Pipelines → Runs → detective-suite <run-name>**.

## Parallel repeat runs and majority vote

Repeat runs of the same cases can run as separate jobs at the same time, one
run folder each (`--run-index N` writes `run<N>`):

```bash
for i in 1 2 3; do python -m scripts.detective_job submit --repo "$REPO" \
    --variant C --run-index $i --output-dir /Volumes/workspace/default/detective_runs/<name>; done
python -m scripts.ensemble /Volumes/workspace/default/detective_runs/<name> --groups 1,2,3
```

`ensemble.py` combines runs by majority vote, scores the result, ranks the
review queue and reports agreement between ensembles and between single runs.

## Inspect a run

```bash
python -m scripts.inspect_detective_run /Volumes/workspace/default/detective_runs/<run-name>/run1/CHG-001.json
```

Shows status, coverage, step errors by type, the action sequence, verifier
outcomes and example UNCERTAIN cases with the raw verifier reply.

Per-case files in `<output-dir>/run<N>/`: `<case>.json` (state, trace,
findings, verified findings, coverage), `<case>.calls.json` (every prompt and
reply), `metrics.json` (per-case and pooled metrics).

## Single case and replay

```bash
python -m scripts.export_case --change-id CHG-001 --output /tmp/case.json
python -m scripts.run_detective --case /tmp/case.json --max-steps 60 --output /tmp/run/result.json
python -m scripts.run_detective --case /tmp/case.json --max-steps 60 \
    --replay /tmp/run/result.calls.json --output /tmp/run/replay.json
```

Replay feeds saved replies back and fails if any prompt differs, which checks
that code or case changes have not altered behaviour.

## Presentation app

```bash
cd /tmp/pci && python -m scripts.deploy_app          # upload, create or update, grant, deploy
python -m scripts.deploy_app --status                # URL and state
```

Or in the UI: **Compute → Apps → control-impact-detective → Deploy**, with the
source folder set to the repository root (the folder holding `app.yaml`), not
`app/`. After a `git pull` in the Git folder, click **Deploy** again.

The app reads `/Volumes/workspace/default/detective_runs` with its own service
principal (granted READ VOLUME by the script) and answers questions with the
`databricks-gpt-oss-120b` endpoint (attached as an app resource). Run locally
with `RESULTS_ROOT=<folder> streamlit run app/app.py`.

## Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| Steps fail with `Expecting value: line 1 column 1` and raw reply `''` | gpt-oss ended with reasoning only | Already handled by retries; run `probe_model`. If it persists, check the endpoint |
| `the JSON object must be str, bytes or bytearray, not list` | Old adapter code | `git pull`; content blocks are now parsed |
| `Unknown tool` with `{"tool": …}` replies | Old code | `git pull` |
| `ModuleNotFoundError: scripts.detective` | Importing from `/Workspace` after a pull | Use the `/tmp/pci` working copy |
| `PermissionError` or `Required key not available` on output paths | Workspace folder or detached process cannot write | Write to a volume; submit as a job |
| Terminal disconnects or `[1]+ Stopped` | Web terminal limits | Submit as a job; or resubmit, which resumes |
| `status` shows the same step count twice | Checks seconds apart (about 10 s per step) | Wait a minute |
