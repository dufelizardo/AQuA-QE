from __future__ import annotations
import time, os
import httpx
from ai_gateway.contracts import IAIGateway, PromptRequest, PromptResponse, ModelProvider

_MODELS = {"low": "claude-haiku-4-5-20251001", "medium": "claude-sonnet-4-6", "high": "claude-sonnet-4-6"}
_COST = {"claude-haiku-4-5-20251001": (0.0008, 0.004), "claude-sonnet-4-6": (0.003, 0.015)}


class ClaudeAdapter(IAIGateway):
    def __init__(self) -> None:
        self._api_key = os.environ["ANTHROPIC_API_KEY"]
        self._base = "https://api.anthropic.com/v1"

    def _headers(self) -> dict:
        return {"x-api-key": self._api_key, "anthropic-version": "2023-06-01", "content-type": "application/json"}

    def complete(self, request: PromptRequest) -> PromptResponse:
        model = _MODELS.get(request.cost_budget or "medium", "claude-sonnet-4-6")
        t0 = time.monotonic()
        payload = {"model": model, "max_tokens": request.max_tokens,
                   "system": request.system, "messages": [{"role": "user", "content": request.user}]}
        with httpx.Client(timeout=90) as client:
            resp = client.post(f"{self._base}/messages", json=payload, headers=self._headers())
        resp.raise_for_status()
        data = resp.json()
        latency_ms = int((time.monotonic() - t0) * 1000)
        usage = data.get("usage", {})
        ti, to = usage.get("input_tokens", 0), usage.get("output_tokens", 0)
        ci, co = _COST.get(model, (0, 0))
        return PromptResponse(
            content=data["content"][0]["text"], provider_used=ModelProvider.CLAUDE, model_used=model,
            tokens_in=ti, tokens_out=to, latency_ms=latency_ms, cost_usd=round(ti/1000*ci + to/1000*co, 6),
        )

    async def complete_async(self, request: PromptRequest) -> PromptResponse:
        return self.complete(request)
