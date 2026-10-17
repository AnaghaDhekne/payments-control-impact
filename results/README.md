# Run results snapshot

`detective_runs.tar.gz` is a copy of the Databricks results volume
(`/Volumes/workspace/default/detective_runs`) taken 2026-10-17 10:35 CT, so the
runs can continue in another workspace. Per-case result files only; the full
model-call logs (`*.calls.json`) are left out.

| Folder | Contents |
|---|---|
| `heldout-final/` | Held-out test, 18 cases, variant A (final, 78.5%) |
| `suite-10/`, `suite-12/` | Frozen check (A) and A/B test (B), 8 cases |
| `suite-11/` | Consistency, 3 cases x 5 runs |
| `fresh-C/run1..6`, `fresh-A/run1..2` | Fresh-damage test, in progress (12-14 of 18 cases per main run) |

Restore into a workspace's volume (from the repository folder):

```bash
tar -xzf results/detective_runs.tar.gz --no-same-owner -C /Volumes/workspace/default/detective_runs
```

Resubmitting a run with `--resume` (always on for jobs) and `--ignore-lock`
continues each case from its last saved step.
