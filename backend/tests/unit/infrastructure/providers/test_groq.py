from __future__ import annotations

import httpx
import pytest
import respx

from ytforge.application.dto.llm import LLMMessage, LLMRequest
from ytforge.infrastructure.providers.errors import ProviderAuthError, ProviderRequestError
from ytforge.infrastructure.providers.llm.groq import GroqProvider


def _request() -> LLMRequest:
    return LLMRequest(model="llama-3.3-70b-versatile", messages=[LLMMessage(role="user", content="hello")])


@respx.mock
async def test_complete_parses_content_and_usage() -> None:
    respx.post("https://api.groq.com/openai/v1/chat/completions").mock(
        return_value=httpx.Response(
            200,
            json={
                "choices": [{"message": {"content": "hi there"}}],
                "usage": {"prompt_tokens": 10, "completion_tokens": 5},
            },
        )
    )
    provider = GroqProvider(api_key="gsk-test", cost_per_1k_tokens_usd=0.01)

    response = await provider.complete(_request())

    assert response.content == "hi there"
    assert response.input_tokens == 10
    assert response.output_tokens == 5
    assert response.cost_usd == pytest.approx(0.00015)


@respx.mock
async def test_complete_sends_authorization_header() -> None:
    route = respx.post("https://api.groq.com/openai/v1/chat/completions").mock(
        return_value=httpx.Response(200, json={"choices": [{"message": {"content": "ok"}}], "usage": {}})
    )
    provider = GroqProvider(api_key="gsk-test")

    await provider.complete(_request())

    request = route.calls.last.request
    assert request.headers["Authorization"] == "Bearer gsk-test"


@respx.mock
async def test_complete_raises_auth_error_on_401() -> None:
    respx.post("https://api.groq.com/openai/v1/chat/completions").mock(
        return_value=httpx.Response(401, json={"error": "invalid api key"})
    )
    provider = GroqProvider(api_key="bad-key")

    with pytest.raises(ProviderAuthError):
        await provider.complete(_request())


@respx.mock
async def test_complete_raises_request_error_on_500() -> None:
    respx.post("https://api.groq.com/openai/v1/chat/completions").mock(return_value=httpx.Response(500, text="oops"))
    provider = GroqProvider(api_key="gsk-test")

    with pytest.raises(ProviderRequestError):
        await provider.complete(_request())


async def test_embed_is_not_supported() -> None:
    provider = GroqProvider(api_key="gsk-test")

    with pytest.raises(ProviderRequestError):
        await provider.embed(["a"], model="n/a")


@respx.mock
async def test_stream_yields_deltas_then_final_chunk() -> None:
    sse_body = (
        'data: {"choices":[{"delta":{"content":"Hel"}}]}\n\n'
        'data: {"choices":[{"delta":{"content":"lo"}}]}\n\n'
        "data: [DONE]\n\n"
    )
    respx.post("https://api.groq.com/openai/v1/chat/completions").mock(
        return_value=httpx.Response(200, text=sse_body, headers={"content-type": "text/event-stream"})
    )
    provider = GroqProvider(api_key="gsk-test")

    chunks = [chunk async for chunk in provider.stream(_request())]

    deltas = [c.delta for c in chunks if not c.is_final]
    assert "".join(deltas) == "Hello"
    assert chunks[-1].is_final
