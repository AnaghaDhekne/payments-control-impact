"""Databricks model-serving adapter for the hybrid evaluator and detective."""

from __future__ import annotations

import json
import time

_MEANINGFUL_KEYS = {
    "action",
    "tool",
    "name",
    "function",
    "findings",
    "decision",
    "recommendations",
    "proposals",
}


def _last_json_object(text: str):
    """Return the last meaningful JSON object embedded in text, re-serialised, or None.

    Only objects carrying a command, finding or result key count: reasoning text
    often mentions fragments such as ``trace_metadata {}`` that are not answers.
    Nested objects inside a parsed object are skipped.
    """
    decoder = json.JSONDecoder()
    found = None
    i = text.find("{")
    while i != -1:
        try:
            obj, end = decoder.raw_decode(text, i)
        except json.JSONDecodeError:
            i = text.find("{", i + 1)
            continue
        if isinstance(obj, dict) and _MEANINGFUL_KEYS & set(obj):
            found = obj
            i = text.find("{", end)
        else:
            i = text.find("{", i + 1)
    return json.dumps(found) if found is not None else None


def _reasoning_text(block: dict) -> str:
    """Collect readable text from a reasoning block (summary items, text or content)."""
    parts = []
    for key in ("summary", "content"):
        items = block.get(key)
        if isinstance(items, str):
            parts.append(items)
        elif isinstance(items, list):
            for item in items:
                if isinstance(item, str):
                    parts.append(item)
                elif isinstance(item, dict) and isinstance(item.get("text"), str):
                    parts.append(item["text"])
    if isinstance(block.get("text"), str):
        parts.append(block["text"])
    return "\n".join(parts)


def content_text(content) -> str:
    """Return the answer text from a chat message content field.

    Reasoning models served on Databricks (for example databricks-gpt-oss-120b)
    return content as a list of blocks such as
    [{"type": "reasoning", ...}, {"type": "text", "text": "..."}].
    Answer ("text") blocks are returned and reasoning is dropped. If the model
    stopped without any answer block (gpt-oss sometimes ends inside its
    reasoning), the last JSON object found in the reasoning is returned instead;
    if there is none, the result is "". Plain strings are returned unchanged.
    """
    if content is None:
        return ""
    if isinstance(content, str):
        # Some SDK versions hand back the block list JSON-encoded as a string.
        stripped = content.lstrip()
        if stripped.startswith("[") and '"type"' in stripped[:200]:
            try:
                decoded = json.loads(stripped)
            except json.JSONDecodeError:
                return content
            if isinstance(decoded, list) and all(isinstance(b, dict) for b in decoded):
                return content_text(decoded)
        return content
    if isinstance(content, dict):
        content = [content]
    if isinstance(content, list):
        parts, reasoning = [], []
        for block in content:
            if isinstance(block, str):
                parts.append(block)
            elif isinstance(block, dict):
                if block.get("type") in ("text", "output_text", None):
                    text = block.get("text")
                    if isinstance(text, str):
                        parts.append(text)
                elif block.get("type") == "reasoning":
                    reasoning.append(_reasoning_text(block))
        answer = "\n".join(parts)
        if answer.strip():
            return answer
        return _last_json_object("\n".join(reasoning)) or ""
    return str(content)


class DatabricksChatLLM:
    def __init__(
        self,
        model="databricks-llama-4-maverick",
        temperature=0.0,
        max_tokens=3000,
        retries=3,
        backoff_seconds=2.0,
    ):
        """Create a WorkspaceClient using SDK-managed environment authentication."""
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.retries = retries
        self.backoff_seconds = backoff_seconds
        from databricks.sdk import WorkspaceClient

        self._w = WorkspaceClient()

    SYSTEM = (
        "Always write your final answer as a single JSON object in the final response, "
        "not only in your reasoning. Never leave the final answer empty."
    )

    def __call__(self, prompt):
        """Query the configured endpoint and return its answer text.

        Endpoint errors and empty answers are retried with backoff. After the
        last attempt an endpoint error is raised; an empty answer is returned
        as "" so the caller records it as a step error.
        """
        from databricks.sdk.service.serving import ChatMessage, ChatMessageRole

        last, text = None, ""
        for attempt in range(self.retries):
            try:
                resp = self._w.serving_endpoints.query(
                    name=self.model,
                    messages=[
                        ChatMessage(role=ChatMessageRole.SYSTEM, content=self.SYSTEM),
                        ChatMessage(role=ChatMessageRole.USER, content=prompt),
                    ],
                    temperature=self.temperature,
                    max_tokens=self.max_tokens,
                )
                text = content_text(resp.choices[0].message.content)
                if text.strip():
                    return text
                last = None  # empty answer: retry without waiting long
                continue
            except Exception as exc:  # endpoint/network errors
                last = exc
                if attempt + 1 < self.retries:
                    time.sleep(self.backoff_seconds * (2**attempt))
        if last is not None:
            raise last
        return text
