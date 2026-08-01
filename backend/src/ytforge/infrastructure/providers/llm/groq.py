from __future__ import annotations

import json
from collections.abc import AsyncIterator

import httpx

from ytforge.application.dto.llm import LLMChunk, LLMRequest, LLMResponse
from ytforge.application.dto.vector import Vector
from ytforge.infrastructure.providers.errors import ProviderRequestError
from ytforge.infrastructure.providers.http_base import ProviderHttpClient
from ytforge.infrastructure.telemetry.provider_metrics import record_provider_call

_BASE_URL = "https://api.groq.com/openai/v1"


class GroqProvider:
    """Groq's OpenAI-compatible Chat Completions API — a genuinely free
    (no card required) fast-inference fallback for text-only LLM routes.
    https://console.groq.com/docs/api-reference No embeddings endpoint;
    `embed` always fails so a route that lists groq for embeddings falls
    through to the next candidate instead of getting a route mismatch."""

    def __init__(self, api_key: str, cost_per_1k_tokens_usd: float | None = None) -> None:
        self._client = ProviderHttpClient("groq", _BASE_URL, {"Authorization": f"Bearer {api_key}"})
        self._api_key = api_key
        self._cost_per_1k = cost_per_1k_tokens_usd

    async def complete(self, req: LLMRequest) -> LLMResponse:
        async with record_provider_call("groq", "llm.complete") as metric:
            body = await self._client.post_json(
                "/chat/completions",
                {
                    "model": req.model,
                    "messages": [{"role": m.role, "content": m.content} for m in req.messages],
                    "temperature": req.temperature,
                    **({"max_tokens": req.max_tokens} if req.max_tokens else {}),
                },
            )
            usage = body.get("usage", {})
            input_tokens = usage.get("prompt_tokens", 0)
            output_tokens = usage.get("completion_tokens", 0)
            content = body["choices"][0]["message"]["content"]
            cost = self._estimate_cost(input_tokens + output_tokens)
            metric.cost_usd = cost
            return LLMResponse(
                content=content,
                model=req.model,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                latency_ms=0,
                cost_usd=cost,
            )

    async def stream(self, req: LLMRequest) -> AsyncIterator[LLMChunk]:
        async with record_provider_call("groq", "llm.stream"), httpx.AsyncClient(
            base_url=_BASE_URL, headers={"Authorization": f"Bearer {self._api_key}"}
        ) as client, client.stream(
            "POST",
            "/chat/completions",
            json={
                "model": req.model,
                "messages": [{"role": m.role, "content": m.content} for m in req.messages],
                "temperature": req.temperature,
                "stream": True,
            },
        ) as response:
            if response.status_code >= 400:
                body = await response.aread()
                raise ProviderRequestError("groq", f"HTTP {response.status_code}: {body[:200]!r}")
            async for line in response.aiter_lines():
                if not line.startswith("data: "):
                    continue
                payload = line.removeprefix("data: ").strip()
                if payload == "[DONE]":
                    yield LLMChunk(delta="", is_final=True)
                    return
                chunk = json.loads(payload)
                delta = chunk["choices"][0]["delta"].get("content", "")
                if delta:
                    yield LLMChunk(delta=delta)

    async def embed(self, texts: list[str], model: str) -> list[Vector]:
        raise ProviderRequestError("groq", "Groq has no embeddings endpoint")

    def _estimate_cost(self, total_tokens: int) -> float | None:
        if self._cost_per_1k is None:
            return None
        return round((total_tokens / 1000) * self._cost_per_1k, 6)
