from __future__ import annotations

from ytforge.infrastructure.config.settings import ModelRoute
from ytforge.infrastructure.providers.errors import ProviderRequestError
from ytforge.infrastructure.providers.registry import ProviderRegistries
from ytforge.interfaces.activities.pipeline_activities import _evaluate_preflight


class _Provider:
    """Minimal LLM/Image/Video/TTS-shaped stand-in — `_evaluate_preflight`
    only ever calls `health_check()`, so that's the only real method."""

    def __init__(self, *, healthy: bool = True, error: str = "unreachable") -> None:
        self._healthy = healthy
        self._error = error
        self.calls = 0

    async def health_check(self) -> None:
        self.calls += 1
        if not self._healthy:
            raise ProviderRequestError("test", self._error)


_ALL_ROUTE_NAMES = [
    "research_summary",
    "embeddings",
    "script_writing",
    "fact_checking",
    "storyboard",
    "voice_direction",
    "seo",
    "image_generation",
    "video_generation",
    "voice_synthesis",
]


def _healthy_registries() -> ProviderRegistries:
    llm = _Provider()
    image = _Provider()
    video = _Provider()
    tts = _Provider()
    return ProviderRegistries(
        llm={"anthropic": llm},
        image={"pollinations": image},
        video={"runway": video},
        tts={"kokoro": tts},
    )


def _all_routes(*, llm: str = "anthropic/claude", image: str = "pollinations/flux",
                 video: str = "runway/gen4.5", tts: str = "kokoro/kokoro",
                 llm_fallback: list[str] | None = None) -> dict[str, ModelRoute]:
    routes: dict[str, ModelRoute] = {}
    for name in _ALL_ROUTE_NAMES:
        if name == "image_generation":
            routes[name] = ModelRoute(primary=image, fallback=[])
        elif name == "video_generation":
            routes[name] = ModelRoute(primary=video, fallback=[])
        elif name == "voice_synthesis":
            routes[name] = ModelRoute(primary=tts, fallback=[])
        else:
            routes[name] = ModelRoute(primary=llm, fallback=llm_fallback or [])
    return routes


async def test_preflight_passes_when_every_route_has_a_healthy_primary() -> None:
    result = await _evaluate_preflight(_all_routes(), _healthy_registries())

    assert result.ok
    assert result.errors == []


async def test_preflight_dedupes_health_checks_for_a_provider_shared_across_routes() -> None:
    """anthropic is the primary for 7 of the 10 preflight routes — it
    should only be pinged once, not 7 times."""
    shared = _Provider()
    registries = ProviderRegistries(
        llm={"anthropic": shared},
        image={"pollinations": _Provider()},
        video={"runway": _Provider()},
        tts={"kokoro": _Provider()},
    )

    result = await _evaluate_preflight(_all_routes(), registries)

    assert result.ok
    assert shared.calls == 1


async def test_preflight_passes_when_primary_unhealthy_but_fallback_is_healthy() -> None:
    registries = ProviderRegistries(
        llm={"anthropic": _Provider(healthy=False), "openai": _Provider(healthy=True)},
        image={"pollinations": _Provider()},
        video={"runway": _Provider()},
        tts={"kokoro": _Provider()},
    )
    routes = _all_routes(llm_fallback=["openai/gpt-4.1"])

    result = await _evaluate_preflight(routes, registries)

    assert result.ok
    assert result.errors == []


async def test_preflight_fails_when_a_route_has_no_healthy_candidate() -> None:
    registries = ProviderRegistries(
        llm={"anthropic": _Provider()},
        image={"pollinations": _Provider()},
        video={"runway": _Provider()},
        tts={"kokoro": _Provider(healthy=False, error="connection refused")},
    )

    result = await _evaluate_preflight(_all_routes(), registries)

    assert not result.ok
    assert len(result.errors) == 1
    assert "voice_synthesis" in result.errors[0]
    assert "connection refused" in result.errors[0]


async def test_preflight_treats_unregistered_provider_as_not_configured() -> None:
    """No comfyui entry in the image registry at all — same "not
    configured" treatment ConfigDrivenModelRouter gives an unregistered
    provider name in a route's chain."""
    registries = ProviderRegistries(
        llm={"anthropic": _Provider()},
        image={},
        video={"runway": _Provider()},
        tts={"kokoro": _Provider()},
    )

    result = await _evaluate_preflight(_all_routes(), registries)

    assert not result.ok
    assert "image_generation" in result.errors[0]
    assert "not configured" in result.errors[0]


async def test_preflight_reports_every_failing_route_not_just_the_first() -> None:
    registries = ProviderRegistries(
        llm={"anthropic": _Provider()},
        image={},
        video={},
        tts={},
    )

    result = await _evaluate_preflight(_all_routes(), registries)

    assert not result.ok
    failing_routes = {"image_generation", "video_generation", "voice_synthesis"}
    assert failing_routes <= {err.split(":")[0] for err in result.errors}
