# Run results snapshot

`detective_runs.tar.gz` is a copy of the Databricks results volume
(`/Volumes/workspace/default/detective_runs`) taken 2026-10-18 12:00 CT from the second
workspace, after every run finished. Per-case result files only; the full
model-call logs (`*.calls.json`) are left out.

| Folder | Contents |
|---|---|
| `heldout-final/` | Held-out test, 18 cases, variant A (final, 78.5%) |
| `suite-10/`, `suite-12/` | Frozen check (A) and A/B test (B), 8 cases |
| `suite-11/` | Consistency, 3 cases x 5 runs |
| `fresh-C/run1..6`, `fresh-A/run1..2` | Fresh-damage test of version C vs A, complete (18 cases each) |
| `freshdev_runs.tar.gz` (separate file) | Final bounded round: A vs D, 5 development cases, 2 runs each |
| `tiebreak_runs.tar.gz` (separate file) | Paired test: tie-break applied to saved A runs (`tb-*`) |
| `suite-09/` | Tuned development cases CHG-014, 025, 017 |

Restore into a workspace's volume (from the repository folder):

```bash
tar -xzf results/detective_runs.tar.gz --no-same-owner -C /Volumes/workspace/default/detective_runs
```

Resubmitting a run with `--resume` (always on for jobs) and `--ignore-lock`
continues each case from its last saved step.
