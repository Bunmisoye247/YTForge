from __future__ import annotations

import json
from collections.abc import AsyncIterator

import httpx

from ytforge.application.dto.llm import LLMChunk, LLMRequest, LLMResponse
from ytforge.application.dto.vector import Vector
from ytforge.infrastructure.providers.errors import ProviderRequestError
from ytforge.infrastructure.providers.http_base import ProviderHttpClient
from ytforge.infrastructure.telemetry.provider_metrics import record_provider_call


class OllamaProvider:
    """Local Ollama server. https://github.com/ollama/ollama/blob/main/docs/api.md
    Free/local — cost is always 0."""

    def __init__(self, base_url: str) -> None:
        self._base_url = base_url
        self._client = ProviderHttpClient("ollama", base_url)

    async def complete(self, req: LLMRequest) -> LLMResponse:
        async with record_provider_call("ollama", "llm.complete") as metric:
            body = await self._client.post_json(
                "/api/chat",
                {
                    "model": req.model,
                    "messages": [{"role": m.role, "content": m.content} for m in req.messages],
                    "stream": False,
                    "options": {"temperature": req.temperature},
                },
            )
            input_tokens = body.get("prompt_eval_count", 0)
            output_tokens = body.get("eval_count", 0)
            metric.cost_usd = 0.0
            return LLMResponse(
                content=body["message"]["content"],
                model=req.model,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                latency_ms=0,
                cost_usd=0.0,
            )

    async def stream(self, req: LLMRequest) -> AsyncIterator[LLMChunk]:
        async with (
            record_provider_call("ollama", "llm.stream"),
            httpx.AsyncClient(base_url=self._base_url) as client,
            client.stream(
                "POST",
                "/api/chat",
                json={
                    "model": req.model,
                    "messages": [{"role": m.role, "content": m.content} for m in req.messages],
                    "stream": True,
                },
            ) as response,
        ):
            if response.status_code >= 400:
                raw = await response.aread()
                raise ProviderRequestError("ollama", f"HTTP {response.status_code}: {raw[:200]!r}")
            async for line in response.aiter_lines():
                if not line.strip():
                    continue
                chunk = json.loads(line)
                if chunk.get("done"):
                    yield LLMChunk(delta="", is_final=True)
                    return
                yield LLMChunk(delta=chunk.get("message", {}).get("content", ""))

    async def embed(self, texts: list[str], model: str) -> list[Vector]:
        async with record_provider_call("ollama", "llm.embed"):
            vectors: list[Vector] = []
            for text in texts:
                body = await self._client.post_json("/api/embeddings", {"model": model, "prompt": text})
                vectors.append(body["embedding"])
            return vectors

    async def health_check(self) -> None:
        # ARCHITECTURE.md §4.3's documented discovery endpoint.
        await self._client.ping("/api/tags")
