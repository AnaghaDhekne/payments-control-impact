"""Databricks model-serving adapter for the hybrid evaluator."""
from __future__ import annotations

class DatabricksChatLLM:
    def __init__(self,model="system.ai.llama-4-maverick",temperature=0.0,max_tokens=3000):
        self.model=model; self.temperature=temperature; self.max_tokens=max_tokens
        from databricks.sdk import WorkspaceClient
        self.client=WorkspaceClient().serving_endpoints.get_open_ai_client()

    def __call__(self,prompt):
        response=self.client.chat.completions.create(
            model=self.model,
            messages=[{"role":"user","content":prompt}],
            temperature=self.temperature,max_tokens=self.max_tokens)
        return response.choices[0].message.content
