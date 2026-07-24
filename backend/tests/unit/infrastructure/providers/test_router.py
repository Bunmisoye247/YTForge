from __future__ import annotations

import pytest

from ytforge.application.dto.llm import LLMRequest, LLMResponse
from ytforge.infrastructure.config.settings import ModelRoute
from ytforge.infrastructure.providers.errors import AllProvidersExhaustedError, ProviderRequestError
from ytforge.infrastructure.providers.registry import ProviderRegistries
from ytforge.infrastructure.providers.router import ConfigDrivenModelRouter


class _AlwaysFailsLLM:
    async def complete(self, req: LLMRequest) -> LLMResponse:
        raise ProviderRequestError("always_fails", "simulated failure")

    async def embed(self, texts: list[str], model: str) -> list[list[float]]:
        raise ProviderRequestError("always_fails", "simulated failure")


class _EchoLLM:
    async def complete(self, req: LLMRequest) -> LLMResponse:
        return LLMResponse(content=f"echo:{req.model}", model=req.model, input_tokens=1, output_tokens=1, latency_ms=1)

    async def embed(self, texts: list[str], model: str) -> list[list[float]]:
        return [[0.0] for _ in texts]


def _make_request() -> LLMRequest:
    return LLMRequest(model="", messages=[])


async def test_router_uses_primary_when_it_succeeds() -> None:
    routes = {"script_writing": ModelRoute(primary="alpha/model-a", fallback=["beta/model-b"])}
    registries = ProviderRegistries(llm={"alpha": _EchoLLM(), "beta": _EchoLLM()})
    router = ConfigDrivenModelRouter(routes, registries)

    response = await router.complete("script_writing", _make_request())

    assert response.content == "echo:model-a"


async def test_router_falls_back_when_primary_fails() -> None:
    routes = {"script_writing": ModelRoute(primary="alpha/model-a", fallback=["beta/model-b"])}
    registries = ProviderRegistries(llm={"alpha": _AlwaysFailsLLM(), "beta": _EchoLLM()})
    router = ConfigDrivenModelRouter(routes, registries)

    response = await router.complete("script_writing", _make_request())

    assert response.content == "echo:model-b"


async def test_router_falls_back_when_primary_provider_not_configured() -> None:
    routes = {"script_writing": ModelRoute(primary="alpha/model-a", fallback=["beta/model-b"])}
    registries = ProviderRegistries(llm={"beta": _EchoLLM()})  # "alpha" never registered
    router = ConfigDrivenModelRouter(routes, registries)

    response = await router.complete("script_writing", _make_request())

    assert response.content == "echo:model-b"


async def test_router_raises_when_all_providers_exhausted() -> None:
    routes = {"script_writing": ModelRoute(primary="alpha/model-a", fallback=["beta/model-b"])}
    registries = ProviderRegistries(llm={"alpha": _AlwaysFailsLLM(), "beta": _AlwaysFailsLLM()})
    router = ConfigDrivenModelRouter(routes, registries)

    with pytest.raises(AllProvidersExhaustedError) as exc_info:
        await router.complete("script_writing", _make_request())

    assert len(exc_info.value.attempts) == 2


async def test_router_raises_for_unknown_route() -> None:
    router = ConfigDrivenModelRouter({}, ProviderRegistries())
    with pytest.raises(ValueError, match="no route configured"):
        await router.complete("nonexistent_route", _make_request())
