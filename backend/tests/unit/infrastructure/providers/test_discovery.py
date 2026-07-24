from __future__ import annotations

import httpx
import respx

from fixtures.fakes import FakeUnitOfWork
from ytforge.application.use_cases.model_registry.register_model import (
    RegisterModelInput,
    register_model,
)
from ytforge.domain.enums import ModelAvailability, ModelCapability
from ytforge.infrastructure.config.settings import DiscoveryEndpoint
from ytforge.infrastructure.providers.discovery import run_discovery


@respx.mock
async def test_discovery_registers_newly_found_ollama_models() -> None:
    respx.get("http://localhost:11434/api/tags").mock(
        return_value=httpx.Response(200, json={"models": [{"name": "llama3"}, {"name": "mistral"}]})
    )
    uow = FakeUnitOfWork()
    discovery = {"ollama": DiscoveryEndpoint(base_url="http://localhost:11434", auto_detect=True)}

    await run_discovery(uow, discovery)

    entries = await uow.model_registry.list_all()
    assert {e.model_name for e in entries} == {"llama3", "mistral"}
    assert all(e.provider == "ollama" for e in entries)
    assert all(e.capability == ModelCapability.LLM for e in entries)
    assert all(e.status == ModelAvailability.AVAILABLE for e in entries)


@respx.mock
async def test_discovery_updates_status_of_already_registered_model() -> None:
    respx.get("http://localhost:1234/v1/models").mock(
        return_value=httpx.Response(200, json={"data": [{"id": "local-model"}]})
    )
    uow = FakeUnitOfWork()
    existing = await register_model(
        uow,
        RegisterModelInput(
            provider="lmstudio",
            model_name="local-model",
            capability=ModelCapability.LLM,
            status=ModelAvailability.UNAVAILABLE,
        ),
    )

    discovery = {"lmstudio": DiscoveryEndpoint(base_url="http://localhost:1234", auto_detect=True)}
    await run_discovery(uow, discovery)

    refreshed = await uow.model_registry.get_by_id(existing.id)
    assert refreshed is not None
    assert refreshed.status == ModelAvailability.AVAILABLE


@respx.mock
async def test_discovery_registers_comfyui_checkpoints() -> None:
    respx.get("http://localhost:8188/object_info").mock(
        return_value=httpx.Response(
            200,
            json={
                "CheckpointLoaderSimple": {
                    "input": {"required": {"ckpt_name": [["sd_xl_base.safetensors", "sd_xl_refiner.safetensors"]]}}
                }
            },
        )
    )
    uow = FakeUnitOfWork()
    discovery = {"comfyui": DiscoveryEndpoint(base_url="http://localhost:8188", auto_detect=True)}

    await run_discovery(uow, discovery)

    entries = await uow.model_registry.list_all()
    assert {e.model_name for e in entries} == {"sd_xl_base.safetensors", "sd_xl_refiner.safetensors"}
    assert all(e.capability == ModelCapability.IMAGE for e in entries)


async def test_discovery_swallows_connection_failure_without_raising() -> None:
    uow = FakeUnitOfWork()
    # No respx mock registered at all -> httpx raises a ConnectError,
    # which must be caught and logged, never propagated.
    discovery = {"ollama": DiscoveryEndpoint(base_url="http://localhost:19999", auto_detect=True)}

    await run_discovery(uow, discovery)

    assert await uow.model_registry.list_all() == []


@respx.mock
async def test_discovery_skips_endpoints_with_auto_detect_disabled() -> None:
    route = respx.get("http://localhost:11434/api/tags").mock(
        return_value=httpx.Response(200, json={"models": [{"name": "llama3"}]})
    )
    uow = FakeUnitOfWork()
    discovery = {"ollama": DiscoveryEndpoint(base_url="http://localhost:11434", auto_detect=False)}

    await run_discovery(uow, discovery)

    assert not route.called
    assert await uow.model_registry.list_all() == []


async def test_discovery_skips_unknown_provider_without_raising() -> None:
    uow = FakeUnitOfWork()
    discovery = {"some_unregistered_provider": DiscoveryEndpoint(base_url="http://localhost:1", auto_detect=True)}

    await run_discovery(uow, discovery)

    assert await uow.model_registry.list_all() == []
