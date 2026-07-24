from __future__ import annotations

from collections.abc import AsyncIterator

from ytforge.application.dto.llm import LLMChunk, LLMRequest, LLMResponse
from ytforge.application.dto.vector import Vector
from ytforge.infrastructure.providers.http_base import ProviderHttpClient
from ytforge.infrastructure.telemetry.provider_metrics import record_provider_call


class LMStudioProvider:
    """Local LM Studio server — OpenAI-compatible `/v1` API.
    https://lmstudio.ai/docs/api Free/local — cost is always 0."""

    def __init__(self, base_url: str) -> None:
        self._client = ProviderHttpClient("lmstudio", base_url)

    async def complete(self, req: LLMRequest) -> LLMResponse:
        async with record_provider_call("lmstudio", "llm.complete") as metric:
            body = await self._client.post_json(
                "/v1/chat/completions",
                {
                    "model": req.model,
                    "messages": [{"role": m.role, "content": m.content} for m in req.messages],
                    "temperature": req.temperature,
                    **({"max_tokens": req.max_tokens} if req.max_tokens else {}),
                },
            )
            usage = body.get("usage", {})
            metric.cost_usd = 0.0
            return LLMResponse(
                content=body["choices"][0]["message"]["content"],
                model=req.model,
                input_tokens=usage.get("prompt_tokens", 0),
                output_tokens=usage.get("completion_tokens", 0),
                latency_ms=0,
                cost_usd=0.0,
            )

    async def stream(self, req: LLMRequest) -> AsyncIterator[LLMChunk]:
        raise NotImplementedError("LM Studio streaming is not implemented in this pass")
        yield  # pragma: no cover

    async def embed(self, texts: list[str], model: str) -> list[Vector]:
        async with record_provider_call("lmstudio", "llm.embed"):
            body = await self._client.post_json("/v1/embeddings", {"model": model, "input": texts})
            return [item["embedding"] for item in body["data"]]
