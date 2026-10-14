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
evidence validation, uncertainty, checkpoints, scoring, and exclusion of
hidden labels. These validate software behavior, not live LLM accuracy.
No Databricks endpoint is available in this editing session. The new detective
has not yet passed a live model evaluation and must not be presented as having
achieved the previous ensemble's metrics.
