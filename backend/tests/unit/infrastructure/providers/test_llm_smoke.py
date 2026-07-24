from __future__ import annotations

import httpx
import respx

from ytforge.application.dto.llm import LLMMessage, LLMRequest
from ytforge.infrastructure.providers.llm.anthropic import AnthropicProvider
from ytforge.infrastructure.providers.llm.gemini import GeminiProvider
from ytforge.infrastructure.providers.llm.lmstudio import LMStudioProvider
from ytforge.infrastructure.providers.llm.ollama import OllamaProvider


def _request() -> LLMRequest:
    return LLMRequest(model="model-x", messages=[LLMMessage(role="user", content="hello")])


@respx.mock
async def test_anthropic_complete_smoke() -> None:
    respx.post("https://api.anthropic.com/v1/messages").mock(
        return_value=httpx.Response(
            200,
            json={
                "content": [{"type": "text", "text": "hi there"}],
                "usage": {"input_tokens": 3, "output_tokens": 2},
            },
        )
    )
    provider = AnthropicProvider(api_key="key-1")

    response = await provider.complete(_request())

    assert response.content == "hi there"


@respx.mock
async def test_gemini_complete_smoke() -> None:
    respx.post(url__regex=r"generativelanguage\.googleapis\.com/v1beta/models/model-x:generateContent.*").mock(
        return_value=httpx.Response(
            200,
            json={
                "candidates": [{"content": {"parts": [{"text": "hi there"}]}}],
                "usageMetadata": {"promptTokenCount": 3, "candidatesTokenCount": 2},
            },
        )
    )
    provider = GeminiProvider(api_key="key-1")

    response = await provider.complete(_request())

    assert response.content == "hi there"


@respx.mock
async def test_gemini_embed_smoke() -> None:
    respx.post(url__regex=r"generativelanguage\.googleapis\.com/v1beta/models/model-x:embedContent.*").mock(
        return_value=httpx.Response(200, json={"embedding": {"values": [0.1, 0.2]}})
    )
    provider = GeminiProvider(api_key="key-1")

    vectors = await provider.embed(["hello"], model="model-x")

    assert vectors == [[0.1, 0.2]]


@respx.mock
async def test_ollama_complete_smoke() -> None:
    respx.post("http://localhost:11434/api/chat").mock(
        return_value=httpx.Response(
            200,
            json={"message": {"content": "hi there"}, "prompt_eval_count": 3, "eval_count": 2},
        )
    )
    provider = OllamaProvider(base_url="http://localhost:11434")

    response = await provider.complete(_request())

    assert response.content == "hi there"
    assert response.cost_usd == 0.0


@respx.mock
async def test_ollama_embed_smoke() -> None:
    respx.post("http://localhost:11434/api/embeddings").mock(
        return_value=httpx.Response(200, json={"embedding": [0.1, 0.2]})
    )
    provider = OllamaProvider(base_url="http://localhost:11434")

    vectors = await provider.embed(["hello"], model="model-x")

    assert vectors == [[0.1, 0.2]]


@respx.mock
async def test_lmstudio_complete_smoke() -> None:
    respx.post("http://localhost:1234/v1/chat/completions").mock(
        return_value=httpx.Response(
            200,
            json={
                "choices": [{"message": {"content": "hi there"}}],
                "usage": {"prompt_tokens": 3, "completion_tokens": 2},
            },
        )
    )
    provider = LMStudioProvider(base_url="http://localhost:1234")

    response = await provider.complete(_request())

    assert response.content == "hi there"
    assert response.cost_usd == 0.0


@respx.mock
async def test_lmstudio_embed_smoke() -> None:
    respx.post("http://localhost:1234/v1/embeddings").mock(
        return_value=httpx.Response(200, json={"data": [{"embedding": [0.1, 0.2]}]})
    )
    provider = LMStudioProvider(base_url="http://localhost:1234")

    vectors = await provider.embed(["hello"], model="model-x")

    assert vectors == [[0.1, 0.2]]
