from __future__ import annotations
import time, os
import httpx
from ai_gateway.contracts import IAIGateway, PromptRequest, PromptResponse, ModelProvider

_MODELS = {"low": "gpt-4o-mini", "medium": "gpt-4o", "high": "gpt-4o"}
_COST = {"gpt-4o-mini": (0.00015, 0.0006), "gpt-4o": (0.005, 0.015)}


class OpenAIAdapter(IAIGateway):
    def __init__(self) -> None:
        self._api_key = os.environ["OPENAI_API_KEY"]
        self._base = "https://api.openai.com/v1"

    def complete(self, request: PromptRequest) -> PromptResponse:
        model = _MODELS.get(request.cost_budget or "medium", "gpt-4o")
        t0 = time.monotonic()
        payload = {"model": model, "max_tokens": request.max_tokens, "temperature": request.temperature,
                   "messages": [{"role": "system", "content": request.system}, {"role": "user", "content": request.user}]}
        with httpx.Client(timeout=60) as client:
            resp = client.post(f"{self._base}/chat/completions", json=payload,
                               headers={"Authorization": f"Bearer {self._api_key}"})
        resp.raise_for_status()
        data = resp.json()
        latency_ms = int((time.monotonic() - t0) * 1000)
        usage = data.get("usage", {})
        ti, to = usage.get("prompt_tokens", 0), usage.get("completion_tokens", 0)
        ci, co = _COST.get(model, (0, 0))
        return PromptResponse(
            content=data["choices"][0]["message"]["content"], provider_used=ModelProvider.OPENAI, model_used=model,
            tokens_in=ti, tokens_out=to, latency_ms=latency_ms, cost_usd=round(ti/1000*ci + to/1000*co, 6),
        )

    async def complete_async(self, request: PromptRequest) -> PromptResponse:
        return self.complete(request)
