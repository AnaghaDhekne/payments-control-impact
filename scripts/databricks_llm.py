"""Databricks model-serving adapter for the hybrid evaluator and detective."""

from __future__ import annotations

import json
import time


def content_text(content) -> str:
    """Return the answer text from a chat message content field.

    Reasoning models served on Databricks (for example databricks-gpt-oss-120b)
    return content as a list of blocks such as
    [{"type": "reasoning", ...}, {"type": "text", "text": "..."}].
    Only the answer ("text") blocks are returned; reasoning blocks are dropped.
    Plain strings are returned unchanged.
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
        parts = []
        for block in content:
            if isinstance(block, str):
                parts.append(block)
            elif isinstance(block, dict) and block.get("type") in (
                "text",
                "output_text",
                None,
            ):
                text = block.get("text")
                if isinstance(text, str):
                    parts.append(text)
        return "\n".join(parts)
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

    def __call__(self, prompt):
        """Query the configured endpoint and return its answer text.

        Transient endpoint errors are retried with backoff; the final error is raised.
        """
        from databricks.sdk.service.serving import ChatMessage, ChatMessageRole

        last = None
        for attempt in range(self.retries):
            try:
                resp = self._w.serving_endpoints.query(
                    name=self.model,
                    messages=[ChatMessage(role=ChatMessageRole.USER, content=prompt)],
                    temperature=self.temperature,
                    max_tokens=self.max_tokens,
                )
                return content_text(resp.choices[0].message.content)
            except Exception as exc:  # endpoint/network errors
                last = exc
                if attempt + 1 < self.retries:
                    time.sleep(self.backoff_seconds * (2**attempt))
        raise last
