"""Answer viewers' questions from the project's own documents and results.

The model sees only the repository documentation bundled with the app and a
summary of the run results the app has loaded; it is told to say so when the
answer is not there. Nothing here reaches the detective or its answer key.
"""

from __future__ import annotations

import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ENDPOINT = os.environ.get("QA_ENDPOINT", "databricks-gpt-oss-120b")
DOC_FILES = [
    "README.md",
    "docs/results.md",
    "docs/evaluation.md",
    "docs/architecture.md",
    "docs/runbook.md",
    "data/README.md",
]

SYSTEM = (
    "Reasoning: low\n"
    "You answer questions about the Payments Control Impact proof of concept for people "
    "across a bank: executives, engineers and controls specialists. Use ONLY the project "
    "material provided. If the material does not answer the question, say so plainly and "
    "name what would answer it. Lead with the direct answer in one or two sentences, then "
    "add detail if useful. Quote exact figures with their case set (tuned, unseen, "
    "held-out) and never present development results as held-out results. Plain language; "
    "define any term a non-specialist may not know. Under 220 words."
)


def project_material(results_summary: str = "") -> str:
    parts = []
    for rel in DOC_FILES:
        p = ROOT / rel
        if p.exists():
            parts.append(f"=== {rel} ===\n{p.read_text(encoding='utf-8')}")
    if results_summary:
        parts.append("=== Live results loaded by the app ===\n" + results_summary)
    return "\n\n".join(parts)


def ask(question: str, history: list[dict], results_summary: str = "") -> str:
    """One answer from the serving endpoint; raises on endpoint errors."""
    from databricks.sdk import WorkspaceClient
    from databricks.sdk.service.serving import ChatMessage, ChatMessageRole

    from scripts.databricks_llm import content_text

    messages = [
        ChatMessage(role=ChatMessageRole.SYSTEM, content=SYSTEM),
        ChatMessage(
            role=ChatMessageRole.USER,
            content="Project material:\n\n" + project_material(results_summary),
        ),
        ChatMessage(
            role=ChatMessageRole.ASSISTANT,
            content="Understood. I will answer only from this material.",
        ),
    ]
    for turn in history[-6:]:
        role = (
            ChatMessageRole.USER
            if turn["role"] == "user"
            else ChatMessageRole.ASSISTANT
        )
        messages.append(ChatMessage(role=role, content=turn["content"]))
    messages.append(ChatMessage(role=ChatMessageRole.USER, content=question))
    w = WorkspaceClient()
    for attempt in range(3):
        resp = w.serving_endpoints.query(
            name=ENDPOINT,
            messages=messages,
            temperature=0.0 if attempt == 0 else 0.3,
            max_tokens=2000,
        )
        text = content_text(resp.choices[0].message.content).strip()
        if text:
            return text
    return "I could not get an answer from the model just now. Please try again, or check the FAQ section."
