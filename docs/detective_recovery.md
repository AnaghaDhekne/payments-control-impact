# Detective path: diagnosis and runnable investigation

## What the saved results establish

`output/heldout_run/heldout_results.json` reports 83 recovered key controls out
of 144 baseline misses (57.6%), and 83 true new controls out of 91 (91.2%).
It separately reports only 23 correct direct edges out of 91 (25.3%). These
are different targets. Correctly naming an affected control does not establish
that a particular source has a direct dependency edge to it.

`review_study_results.json` reports 5.6% recovery and 27.3% approval precision
after an LLM review. This is simulated model review, not human review. The
saved report's attribution to reviewer conservatism alone is incomplete:
many successful control predictions carried incorrect direct-edge claims.
The current precision-review prompt also omits the complete control document
and tells the reviewer to approve when in doubt. Loosening approval cannot
establish correctness.

The previous improved retrieval/ensemble pipeline is described in the
manifest as inline experimental code. The checked-in basic proposer is a
single prompt. Existing successful results therefore do not establish a
reproducible agentic runtime. The final report also contains stale statements
about held-out evaluation and human-review status; use the raw artifacts to
distinguish the two studies.

## Implemented detective workflow

`scripts/detective.py` lets the model choose searches, inspect full control
documents and incident metadata edges, trace existing metadata, and submit
impact hypotheses. It accepts direct or indirect impact with exact evidence
and a causal explanation. A separate model call checks each hypothesis using
the full ticket, document, and visible graph. Disagreement and invalid review
output remain UNCERTAIN. No inferred dependency edges are inserted.

This is a bounded tool-using agent implemented through structured JSON
actions, rather than an SDK-native function-calling interface. The model
chooses its next action after receiving tool observations. Tools are read-only.
Search ranks documents but never excludes zero-overlap controls from the
catalog. Budget exhaustion and uninvestigated controls are explicit; finishing
does not certify complete coverage. The verifier uses the same adapter by
default, so its errors may correlate with the investigator's errors.

## Fixes for the live agentic run (2026-10-14)

Earlier live runs could not produce findings for two reasons, now fixed:

1. **Reasoning-model output was discarded.** `databricks-gpt-oss-120b` returns
   message content as a list of blocks (`reasoning`, then `text`). The adapter
   passed the list through, JSON parsing raised a `TypeError` on every step, and
   the agent ended with no findings. `databricks_llm.content_text()` now keeps only
   the answer text; the detective also normalises any non-string response.
   Symptom in old traces: `the JSON object must be str, bytes or bytearray, not list`.
2. **The step budget could not cover the case.** One control needed one inspect
   step plus one submit step, while cases such as CHG-001 have 49 affected
   controls (19 key) out of 101. The agent can now inspect up to 15 controls and
   submit up to 20 findings per step.

Other changes:

- `explore_node {node_id}` shows a node's name, description and visible in/out
  edges, so the agent can follow the change from the field and see where visible
  lineage breaks (for CHG-001 the field reaches three rules, then nothing).
- Prompts no longer resend the full graph and every past tool output each step.
  A notebook keeps inspected control text and explored nodes; older observations
  are summarised. The first prompt on CHG-001 fell from about 62k to 18k characters.
- An early `finish` while controls are undecided returns a reminder once.
- Findings may carry `evidence_path` (known node IDs). The verifier sees the
  ticket, the control, its visible edges and the path nodes, and gets one retry
  with the validation error when its JSON is invalid.
- `DatabricksChatLLM` retries transient endpoint errors with backoff.

These are software fixes verified with scripted model responses. They do not
show live accuracy; that requires running the suite below.

## Run the development suite

```bash
python -m scripts.run_detective_suite --model databricks-gpt-oss-120b \
    --change-ids CHG-001 --max-steps 60 --output-dir output/runs/detective-suite-01
# read output/runs/detective-suite-01/run1/CHG-001.json (trace) before widening
python -m scripts.run_detective_suite --model databricks-gpt-oss-120b \
    --max-steps 60 --output-dir output/runs/detective-suite-02
```

Labels are computed offline inside the runner and never reach the agent.
Each run writes per-case results, model calls, and `metrics.json`; `--runs 5`
also writes `consistency.json`.

### Note on the frozen gates

On the 36 development cases at 30% change-correlated degradation, the rules
baseline flags 176 controls and misses 225 affected key controls. Recovering
50% of those misses means adding at least 113 controls, which is +64% workload
against the baseline even with perfect precision. If true recoveries count as
workload, the >=50% recovery gate and the <=25% added-workload gate cannot both
pass on this benchmark. Report false-positive workload separately rather than
loosening either gate after the fact.

## Run in Databricks

From the repository root, install the existing development and LLM requirements.
Use workspace SDK authentication; never put tokens in files or commits.

```bash
python -m pip install -r requirements-dev.txt -r requirements-llm.txt
python -m scripts.export_case --change-id CHG-001 --output output/runs/detective-dev/case.json
python -m scripts.run_detective --case output/runs/detective-dev/case.json --model databricks-gpt-oss-120b --max-steps 60 --output output/runs/detective-dev/result.json
```

Use a unique output directory per run. The command writes model prompts and
raw responses to `result.calls.json` after each successful model call and
checkpoints the investigation in `result.json`. Investigative endpoint errors
fail loudly after saving status; verifier errors produce UNCERTAIN. Inspect
the trace for invalid JSON, unsuccessful tool calls, quote errors, early finish,
and unresolved controls before increasing the budget. Each submitted finding
adds one verification call, so max-steps is not a total model-call cap.

Replay checks that each prompt exactly matches the saved transcript:

```bash
python -m scripts.run_detective --case output/runs/detective-dev/case.json --max-steps 60 --replay output/runs/detective-dev/result.calls.json --output output/runs/detective-dev/replay.json
```

## Evaluate without changing the goalposts

The original business question is affected-control discovery. Score that
separately from missing-direct-edge reconstruction. `score_detective.py`
accepts independently supplied labels with `affected_control_ids` and
`key_control_ids`. Never send these labels to the agent. UNCERTAIN counts as
review workload and does not count as recovered. Uninvestigated controls
remain unresolved and key misses remain in the denominator.

```bash
python -m scripts.score_detective --result output/runs/detective-dev/result.json --labels path/to/offline-labels.json --output output/runs/detective-dev/metrics.json
```

First run one development case and inspect the actual model trace. Then run
the full development set, measure recovery, new-control precision, uncertainty,
uninvestigated coverage, repeatability, latency and cost. Include unaffected
cases and indirect-impact cases. Freeze configuration and use fresh scenario
families for final evaluation: the previous held-out cases have now been
inspected during diagnosis. A selected demo is a demonstration, not evidence
of aggregate performance. Keep every failure and earlier artifact.

## Validation status

Automated tests use scripted model responses to check actual tool execution,
evidence validation, uncertainty, checkpoints, resume, scoring, and exclusion
of hidden labels. These validate software behavior, not live LLM accuracy.

Live development runs on Databricks are recorded in
[detective_live_results.md](detective_live_results.md): 22 of 27 key misses
recovered across four development cases, 92% precision on new controls, the
workload gate not met, and consistency not yet measured. These cases were
inspected while fixing the code, so they are not held-out evidence and must not
be presented as having achieved the previous ensemble's held-out metrics.

## Running long jobs

Databricks web terminals end background processes. Submit runs as a job and
write results to a Unity Catalog volume:

```bash
python -m scripts.detective_job submit --repo /Workspace/Users/<you>/payments-control-impact \
    --change-ids CHG-014 CHG-025 CHG-017 \
    --output-dir /Volumes/workspace/default/detective_runs/suite-09
python -m scripts.detective_job status <run_id>
```

Jobs always resume from saved results, so resubmitting continues an
interrupted run.
