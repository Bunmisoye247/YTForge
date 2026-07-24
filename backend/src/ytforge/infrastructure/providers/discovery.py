from __future__ import annotations

import logging

import httpx

from ytforge.application.common.errors import NotFoundError
from ytforge.application.ports.providers import UnitOfWork
from ytforge.application.use_cases.model_registry import (
    RegisterModelInput,
    list_models,
    register_model,
    update_model_status,
)
from ytforge.domain.enums import ModelAvailability, ModelCapability
from ytforge.infrastructure.config.settings import DiscoveryEndpoint

logger = logging.getLogger("ytforge.discovery")

_DISCOVERY_TIMEOUT_S = 3.0


async def _fetch_ollama_models(base_url: str) -> list[str]:
    async with httpx.AsyncClient(base_url=base_url, timeout=_DISCOVERY_TIMEOUT_S) as client:
        response = await client.get("/api/tags")
        response.raise_for_status()
        return [m["name"] for m in response.json().get("models", [])]


async def _fetch_lmstudio_models(base_url: str) -> list[str]:
    async with httpx.AsyncClient(base_url=base_url, timeout=_DISCOVERY_TIMEOUT_S) as client:
        response = await client.get("/v1/models")
        response.raise_for_status()
        return [m["id"] for m in response.json().get("data", [])]


async def _fetch_comfyui_checkpoints(base_url: str) -> list[str]:
    async with httpx.AsyncClient(base_url=base_url, timeout=_DISCOVERY_TIMEOUT_S) as client:
        response = await client.get("/object_info")
        response.raise_for_status()
        body = response.json()
        loader = body.get("CheckpointLoaderSimple", {})
        names = loader.get("input", {}).get("required", {}).get("ckpt_name", [[]])
        return list(names[0]) if names else []


_FETCHERS = {
    "ollama": (_fetch_ollama_models, ModelCapability.LLM),
    "lmstudio": (_fetch_lmstudio_models, ModelCapability.LLM),
    "comfyui": (_fetch_comfyui_checkpoints, ModelCapability.IMAGE),
}


async def run_discovery(uow: UnitOfWork, discovery: dict[str, DiscoveryEndpoint]) -> None:
    """Scans every `auto_detect: true` entry in `settings.models.discovery`.
    A provider that isn't reachable (not running locally) is logged and
    skipped — this must never crash the app, since local model servers are
    optional infrastructure, not a hard dependency (confirmed: none are
    running in this dev environment)."""
    existing = {(e.provider, e.model_name, e.capability): e for e in await list_models(uow)}

    for provider_name, endpoint in discovery.items():
        if not endpoint.auto_detect:
            continue
        fetcher = _FETCHERS.get(provider_name)
        if fetcher is None:
            logger.warning("no discovery fetcher registered for provider %r", provider_name)
            continue
        fetch, capability = fetcher
        try:
            model_names = await fetch(endpoint.base_url)
        except (httpx.HTTPError, KeyError, ValueError) as exc:
            logger.info("discovery skipped for %s (%s): %s", provider_name, endpoint.base_url, exc)
            continue

        for model_name in model_names:
            key = (provider_name, model_name, capability)
            if key in existing:
                try:
                    await update_model_status(uow, existing[key].id, ModelAvailability.AVAILABLE)
                except NotFoundError:
                    continue
            else:
                await register_model(
                    uow,
                    RegisterModelInput(
                        provider=provider_name,
                        model_name=model_name,
                        capability=capability,
                        base_url=endpoint.base_url,
                        status=ModelAvailability.AVAILABLE,
                    ),
                )
