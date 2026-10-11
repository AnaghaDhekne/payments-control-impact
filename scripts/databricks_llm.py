"""Databricks model-serving adapter for the hybrid evaluator."""

from __future__ import annotations


class DatabricksChatLLM:
    def __init__(
        self, model="databricks-llama-4-maverick", temperature=0.0, max_tokens=3000
    ):
        """Create a WorkspaceClient using SDK-managed environment authentication."""
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        from databricks.sdk import WorkspaceClient

        self._w = WorkspaceClient()

    def __call__(self, prompt):
        """Query the configured endpoint and return its text response."""
        from databricks.sdk.service.serving import ChatMessage, ChatMessageRole

        resp = self._w.serving_endpoints.query(
            name=self.model,
            messages=[ChatMessage(role=ChatMessageRole.USER, content=prompt)],
            temperature=self.temperature,
            max_tokens=self.max_tokens,
        )
        return resp.choices[0].message.content
