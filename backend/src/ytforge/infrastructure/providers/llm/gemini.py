from __future__ import annotations

from collections.abc import AsyncIterator

from ytforge.application.dto.llm import LLMChunk, LLMRequest, LLMResponse
from ytforge.application.dto.vector import Vector
from ytforge.infrastructure.providers.http_base import ProviderHttpClient
from ytforge.infrastructure.telemetry.provider_metrics import record_provider_call

_BASE_URL = "https://generativelanguage.googleapis.com/v1beta"


def _to_gemini_role(role: str) -> str:
    return "model" if role == "assistant" else "user"


class GeminiProvider:
    """Google Generative Language API.
    https://ai.google.dev/api/generate-content
    # verify against current provider docs — field names below are a
    # best-effort approximation, unverified against a live endpoint."""

    def __init__(self, api_key: str, cost_per_1k_tokens_usd: float | None = None) -> None:
        self._client = ProviderHttpClient("gemini", _BASE_URL)
        self._api_key = api_key
        self._cost_per_1k = cost_per_1k_tokens_usd

    async def complete(self, req: LLMRequest) -> LLMResponse:
        async with record_provider_call("gemini", "llm.complete") as metric:
            system = next((m.content for m in req.messages if m.role == "system"), None)
            contents = [
                {"role": _to_gemini_role(m.role), "parts": [{"text": m.content}]}
                for m in req.messages
                if m.role != "system"
            ]
            body = await self._client.post_json(
                f"/models/{req.model}:generateContent?key={self._api_key}",
                {
                    "contents": contents,
                    "generationConfig": {
                        "temperature": req.temperature,
                        **({"maxOutputTokens": req.max_tokens} if req.max_tokens else {}),
                    },
                    **({"system_instruction": {"parts": [{"text": system}]}} if system else {}),
                },
            )
            candidate = body["candidates"][0]
            content = "".join(part["text"] for part in candidate["content"]["parts"])
            usage = body.get("usageMetadata", {})
            input_tokens = usage.get("promptTokenCount", 0)
            output_tokens = usage.get("candidatesTokenCount", 0)
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
        # Gemini's streamGenerateContent endpoint returns a JSON array over
        # a chunked response rather than SSE; not implemented in this pass
        # — complete() covers every current agent's needs (none stream yet).
        raise NotImplementedError("Gemini streaming is not implemented in this pass")
        yield  # pragma: no cover - makes this an async generator

    async def embed(self, texts: list[str], model: str) -> list[Vector]:
        async with record_provider_call("gemini", "llm.embed"):
            vectors: list[Vector] = []
            for text in texts:
                body = await self._client.post_json(
                    f"/models/{model}:embedContent?key={self._api_key}",
                    {"content": {"parts": [{"text": text}]}},
                )
                vectors.append(body["embedding"]["values"])
            return vectors

    def _estimate_cost(self, total_tokens: int) -> float | None:
        if self._cost_per_1k is None:
            return None
        return round((total_tokens / 1000) * self._cost_per_1k, 6)
