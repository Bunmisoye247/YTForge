from __future__ import annotations

import httpx
import pytest
import respx

from ytforge.application.dto.llm import LLMMessage, LLMRequest
from ytforge.infrastructure.providers.errors import ProviderAuthError, ProviderRequestError
from ytforge.infrastructure.providers.llm.openai import OpenAIProvider


def _request() -> LLMRequest:
    return LLMRequest(model="gpt-4o", messages=[LLMMessage(role="user", content="hello")])


@respx.mock
async def test_complete_parses_content_and_usage() -> None:
    respx.post("https://api.openai.com/v1/chat/completions").mock(
        return_value=httpx.Response(
            200,
            json={
                "choices": [{"message": {"content": "hi there"}}],
                "usage": {"prompt_tokens": 10, "completion_tokens": 5},
            },
        )
    )
    provider = OpenAIProvider(api_key="sk-test", cost_per_1k_tokens_usd=0.01)

    response = await provider.complete(_request())

    assert response.content == "hi there"
    assert response.input_tokens == 10
    assert response.output_tokens == 5
    assert response.cost_usd == pytest.approx(0.00015)


@respx.mock
async def test_complete_sends_authorization_header_and_body() -> None:
    route = respx.post("https://api.openai.com/v1/chat/completions").mock(
        return_value=httpx.Response(200, json={"choices": [{"message": {"content": "ok"}}], "usage": {}})
    )
    provider = OpenAIProvider(api_key="sk-test")

    await provider.complete(_request())

    request = route.calls.last.request
    assert request.headers["Authorization"] == "Bearer sk-test"
    body = respx.calls.last.request.content
    import json as _json

    parsed = _json.loads(body)
    assert parsed["model"] == "gpt-4o"
    assert parsed["messages"] == [{"role": "user", "content": "hello"}]


@respx.mock
async def test_complete_raises_auth_error_on_401() -> None:
    respx.post("https://api.openai.com/v1/chat/completions").mock(
        return_value=httpx.Response(401, json={"error": "invalid api key"})
    )
    provider = OpenAIProvider(api_key="bad-key")

    with pytest.raises(ProviderAuthError):
        await provider.complete(_request())


@respx.mock
async def test_complete_raises_request_error_on_500() -> None:
    respx.post("https://api.openai.com/v1/chat/completions").mock(return_value=httpx.Response(500, text="oops"))
    provider = OpenAIProvider(api_key="sk-test")

    with pytest.raises(ProviderRequestError):
        await provider.complete(_request())


@respx.mock
async def test_embed_returns_vectors() -> None:
    respx.post("https://api.openai.com/v1/embeddings").mock(
        return_value=httpx.Response(
            200, json={"data": [{"embedding": [0.1, 0.2]}, {"embedding": [0.3, 0.4]}]}
        )
    )
    provider = OpenAIProvider(api_key="sk-test")

    vectors = await provider.embed(["a", "b"], model="text-embedding-3-small")

    assert vectors == [[0.1, 0.2], [0.3, 0.4]]


@respx.mock
async def test_stream_yields_deltas_then_final_chunk() -> None:
    sse_body = (
        'data: {"choices":[{"delta":{"content":"Hel"}}]}\n\n'
        'data: {"choices":[{"delta":{"content":"lo"}}]}\n\n'
        "data: [DONE]\n\n"
    )
    respx.post("https://api.openai.com/v1/chat/completions").mock(
        return_value=httpx.Response(200, text=sse_body, headers={"content-type": "text/event-stream"})
    )
    provider = OpenAIProvider(api_key="sk-test")

    chunks = [chunk async for chunk in provider.stream(_request())]

    deltas = [c.delta for c in chunks if not c.is_final]
    assert "".join(deltas) == "Hello"
    assert chunks[-1].is_final
