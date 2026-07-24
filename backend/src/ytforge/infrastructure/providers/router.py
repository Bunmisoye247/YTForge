from __future__ import annotations

from dataclasses import replace

from ytforge.application.dto.image import ImageAsset, ImageRequest
from ytforge.application.dto.llm import LLMRequest, LLMResponse
from ytforge.application.dto.music import MusicAsset, MusicRequest
from ytforge.application.dto.tts import AudioAsset, TTSRequest
from ytforge.application.dto.vector import Vector
from ytforge.application.dto.video import VideoJob, VideoJobStatus, VideoRequest
from ytforge.infrastructure.config.settings import ModelRoute
from ytforge.infrastructure.providers.errors import AllProvidersExhaustedError, ProviderError
from ytforge.infrastructure.providers.registry import ProviderRegistries


def _split(provider_model: str) -> tuple[str, str]:
    provider, _, model = provider_model.partition("/")
    if not model:
        raise ValueError(f"expected 'provider/model', got {provider_model!r}")
    return provider, model


class ConfigDrivenModelRouter:
    """Resolves `settings.models.routes[route_name]` to a provider
    instance + model name, trying `primary` then `fallback` in order
    (ARCHITECTURE.md §4.3). A provider missing from the registry (not
    configured, per ProviderSettings.is_configured) is treated exactly
    like a failed call — falls through to the next candidate."""

    def __init__(self, routes: dict[str, ModelRoute], registries: ProviderRegistries) -> None:
        self._routes = routes
        self._registries = registries

    def _chain(self, route_name: str) -> list[str]:
        route = self._routes.get(route_name)
        if route is None:
            raise ValueError(f"no route configured for {route_name!r}")
        return [route.primary, *route.fallback]

    async def complete(self, route_name: str, req: LLMRequest) -> LLMResponse:
        errors: list[ProviderError] = []
        for candidate in self._chain(route_name):
            provider_key, model = _split(candidate)
            provider = self._registries.llm.get(provider_key)
            if provider is None:
                errors.append(ProviderError(provider_key, "not configured"))
                continue
            try:
                return await provider.complete(replace(req, model=model))
            except ProviderError as exc:
                errors.append(exc)
        raise AllProvidersExhaustedError(route_name, errors)

    async def embed(self, route_name: str, texts: list[str]) -> list[Vector]:
        errors: list[ProviderError] = []
        for candidate in self._chain(route_name):
            provider_key, model = _split(candidate)
            provider = self._registries.llm.get(provider_key)
            if provider is None:
                errors.append(ProviderError(provider_key, "not configured"))
                continue
            try:
                return await provider.embed(texts, model)
            except ProviderError as exc:
                errors.append(exc)
        raise AllProvidersExhaustedError(route_name, errors)

    async def generate_image(self, route_name: str, req: ImageRequest) -> list[ImageAsset]:
        errors: list[ProviderError] = []
        for candidate in self._chain(route_name):
            provider_key, model = _split(candidate)
            provider = self._registries.image.get(provider_key)
            if provider is None:
                errors.append(ProviderError(provider_key, "not configured"))
                continue
            try:
                return await provider.generate(replace(req, model=model))
            except ProviderError as exc:
                errors.append(exc)
        raise AllProvidersExhaustedError(route_name, errors)

    async def generate_video(self, route_name: str, req: VideoRequest) -> VideoJob:
        errors: list[ProviderError] = []
        for candidate in self._chain(route_name):
            provider_key, model = _split(candidate)
            provider = self._registries.video.get(provider_key)
            if provider is None:
                errors.append(ProviderError(provider_key, "not configured"))
                continue
            try:
                job = await provider.generate(replace(req, model=model))
                return replace(job, provider=provider_key)
            except ProviderError as exc:
                errors.append(exc)
        raise AllProvidersExhaustedError(route_name, errors)

    async def poll_video(self, route_name: str, job: VideoJob) -> VideoJobStatus:
        # poll always targets the exact provider that accepted the job —
        # falling back mid-poll to a different provider makes no sense,
        # since `job.provider_job_id` only means something to the provider
        # that issued it.
        provider = self._registries.video.get(job.provider)
        if provider is None:
            raise AllProvidersExhaustedError(
                route_name, [ProviderError(job.provider, "not configured")]
            )
        return await provider.poll(job)

    async def synthesize_speech(self, route_name: str, req: TTSRequest) -> AudioAsset:
        errors: list[ProviderError] = []
        for candidate in self._chain(route_name):
            provider_key, model = _split(candidate)
            provider = self._registries.tts.get(provider_key)
            if provider is None:
                errors.append(ProviderError(provider_key, "not configured"))
                continue
            try:
                return await provider.synthesize(replace(req, model=model))
            except ProviderError as exc:
                errors.append(exc)
        raise AllProvidersExhaustedError(route_name, errors)

    async def generate_music(self, route_name: str, req: MusicRequest) -> MusicAsset:
        errors: list[ProviderError] = []
        for candidate in self._chain(route_name):
            provider_key, model = _split(candidate)
            provider = self._registries.music.get(provider_key)
            if provider is None:
                errors.append(ProviderError(provider_key, "not configured"))
                continue
            try:
                return await provider.generate(replace(req, model=model))
            except ProviderError as exc:
                errors.append(exc)
        raise AllProvidersExhaustedError(route_name, errors)
