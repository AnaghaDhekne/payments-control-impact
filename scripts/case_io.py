"""Observable-case helpers shared by the detective, exporters and runners.

The observable payload is the only part of a benchmark case the agent may see.
Evaluation-only fields (split, degradation manifest, hidden labels) are dropped.
"""

import hashlib
import json
import re

OBSERVABLE_FIELDS = (
    "change_id",
    "change_ticket",
    "visible_metadata",
    "control_documents",
)


def observable_payload(case):
    """Select the runtime fields allowed in prompts; exclude evaluation-only metadata."""
    return {k: case[k] for k in OBSERVABLE_FIELDS}


def case_digest(case):
    """SHA-256 of the canonical observable case; binds saved runs to their exact input."""
    return hashlib.sha256(
        json.dumps(observable_payload(case), sort_keys=True).encode()
    ).hexdigest()


def extract_json(raw):
    """Extract JSON from a model response that may include prose or markdown fences."""
    try:
        json.loads(raw)
        return raw
    except json.JSONDecodeError:
        pass
    match = re.search(r"```(?:json)?\s*\n?(.*?)\n?```", raw, re.DOTALL)
    if match:
        candidate = match.group(1).strip()
        try:
            json.loads(candidate)
            return candidate
        except json.JSONDecodeError:
            pass
    start, end = raw.find("{"), raw.rfind("}")
    if start != -1 and end > start:
        candidate = raw[start : end + 1]
        try:
            json.loads(candidate)
            return candidate
        except json.JSONDecodeError:
            pass
    return raw
