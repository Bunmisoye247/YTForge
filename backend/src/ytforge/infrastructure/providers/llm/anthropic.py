from __future__ import annotations

import json
from collections.abc import AsyncIterator

import httpx

from ytforge.application.dto.llm import LLMChunk, LLMRequest, LLMResponse
from ytforge.application.dto.vector import Vector
from ytforge.infrastructure.providers.errors import ProviderRequestError
from ytforge.infrastructure.providers.http_base import ProviderHttpClient
from ytforge.infrastructure.telemetry.provider_metrics import record_provider_call

_BASE_URL = "https://api.anthropic.com/v1"
_ANTHROPIC_VERSION = "2023-06-01"


def _split_system(req: LLMRequest) -> tuple[str | None, list[dict[str, str]]]:
    """Anthropic's Messages API takes the system prompt as a separate
    top-level field, not a "system"-role message."""
    system = next((m.content for m in req.messages if m.role == "system"), None)
    turns = [{"role": m.role, "content": m.content} for m in req.messages if m.role != "system"]
    return system, turns


class AnthropicProvider:
    """Anthropic Messages API. https://docs.anthropic.com/en/api/messages"""

    def __init__(self, api_key: str, cost_per_1k_tokens_usd: float | None = None) -> None:
        headers = {
            "x-api-key": api_key,
            "anthropic-version": _ANTHROPIC_VERSION,
        }
        self._client = ProviderHttpClient("anthropic", _BASE_URL, headers)
        self._api_key = api_key
        self._cost_per_1k = cost_per_1k_tokens_usd

    async def complete(self, req: LLMRequest) -> LLMResponse:
        async with record_provider_call("anthropic", "llm.complete") as metric:
            system, turns = _split_system(req)
            body = await self._client.post_json(
                "/messages",
                {
                    "model": req.model,
                    "max_tokens": req.max_tokens or 4096,
                    "temperature": req.temperature,
                    "messages": turns,
                    **({"system": system} if system else {}),
                },
            )
            usage = body.get("usage", {})
            input_tokens = usage.get("input_tokens", 0)
            output_tokens = usage.get("output_tokens", 0)
            content = "".join(block["text"] for block in body["content"] if block["type"] == "text")
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
        async with record_provider_call("anthropic", "llm.stream"):
            system, turns = _split_system(req)
            headers = {"x-api-key": self._api_key, "anthropic-version": _ANTHROPIC_VERSION}
            async with httpx.AsyncClient(base_url=_BASE_URL, headers=headers) as client, client.stream(
                "POST",
                "/messages",
                json={
                    "model": req.model,
                    "max_tokens": req.max_tokens or 4096,
                    "messages": turns,
                    **({"system": system} if system else {}),
                    "stream": True,
                },
            ) as response:
                if response.status_code >= 400:
                    raw = await response.aread()
                    raise ProviderRequestError("anthropic", f"HTTP {response.status_code}: {raw[:200]!r}")
                async for line in response.aiter_lines():
                    if not line.startswith("data: "):
                        continue
                    event = json.loads(line.removeprefix("data: ").strip())
                    if event.get("type") == "content_block_delta":
                        yield LLMChunk(delta=event["delta"].get("text", ""))
                    elif event.get("type") == "message_stop":
                        yield LLMChunk(delta="", is_final=True)
                        return

    async def embed(self, texts: list[str], model: str) -> list[Vector]:
        raise NotImplementedError(
            "Anthropic does not offer an embeddings endpoint — route the "
            "'embeddings' capability to openai or ollama instead."
        )

    def _estimate_cost(self, total_tokens: int) -> float | None:
        if self._cost_per_1k is None:
            return None
        return round((total_tokens / 1000) * self._cost_per_1k, 6)
