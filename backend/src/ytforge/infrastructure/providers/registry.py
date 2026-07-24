from __future__ import annotations

from dataclasses import dataclass, field

from ytforge.application.ports.providers.image_provider import ImageProvider
from ytforge.application.ports.providers.llm_provider import LLMProvider
from ytforge.application.ports.providers.music_provider import MusicProvider
from ytforge.application.ports.providers.object_storage import ObjectStorage
from ytforge.application.ports.providers.tts_provider import TTSProvider
from ytforge.application.ports.providers.video_provider import VideoProvider
from ytforge.infrastructure.config.settings import ProvidersSettings
from ytforge.infrastructure.providers.fakeprovider import (
    FakeImageProvider,
    FakeLLMProvider,
    FakeMusicProvider,
    FakeTTSProvider,
    FakeVideoProvider,
)
from ytforge.infrastructure.providers.image import (
    A1111Provider,
    ComfyUIProvider,
    FluxApiProvider,
    SdxlDiffusersProvider,
)
from ytforge.infrastructure.providers.llm import (
    AnthropicProvider,
    GeminiProvider,
    LMStudioProvider,
    OllamaProvider,
    OpenAIProvider,
)
from ytforge.infrastructure.providers.music import MubertProvider, SunoProvider, UdioProvider
from ytforge.infrastructure.providers.tts import (
    AzureTtsProvider,
    ElevenLabsProvider,
    KokoroProvider,
    PiperProvider,
    PlayHTProvider,
)
from ytforge.infrastructure.providers.video import (
    HailuoProvider,
    KlingProvider,
    LumaProvider,
    RunwayProvider,
    VeoProvider,
)


@dataclass(slots=True)
class ProviderRegistries:
    llm: dict[str, LLMProvider] = field(default_factory=dict)
    image: dict[str, ImageProvider] = field(default_factory=dict)
    video: dict[str, VideoProvider] = field(default_factory=dict)
    tts: dict[str, TTSProvider] = field(default_factory=dict)
    music: dict[str, MusicProvider] = field(default_factory=dict)


def build_fake_registries() -> ProviderRegistries:
    """Every provider name resolves to the same fake instance — a route's
    configured "provider/model" string still gets split and the model name
    still flows into the request, only the transport is faked."""
    return ProviderRegistries(
        llm={name: FakeLLMProvider() for name in ("openai", "anthropic", "gemini", "ollama", "lmstudio")},
        image={name: FakeImageProvider() for name in ("flux_api", "sdxl_diffusers", "comfyui", "a1111")},
        video={name: FakeVideoProvider() for name in ("veo", "runway", "kling", "luma", "hailuo")},
        tts={name: FakeTTSProvider() for name in ("elevenlabs", "playht", "azure_tts", "kokoro", "piper")},
        music={name: FakeMusicProvider() for name in ("suno", "udio", "mubert")},
    )


def build_real_registries(
    providers: ProvidersSettings, storage: ObjectStorage, raw_assets_bucket: str
) -> ProviderRegistries:
    """Only providers with a configured key or base_url get registered — an
    unconfigured provider named in a route's fallback chain just isn't in
    the dict, which `ConfigDrivenModelRouter` treats as "try the next
    fallback" rather than a crash. `storage`/`raw_assets_bucket` (Phase 7)
    let media-producing adapters persist real bytes instead of returning a
    placeholder key — see `A1111Provider`/`RunwayProvider` for the two
    reference patterns (sync bytes vs. download-then-upload)."""
    registries = ProviderRegistries()

    if providers.openai.is_configured:
        registries.llm["openai"] = OpenAIProvider(
            providers.openai.api_key.get_secret_value() if providers.openai.api_key else "",
            providers.openai.cost_per_unit_usd,
        )
    if providers.anthropic.is_configured:
        registries.llm["anthropic"] = AnthropicProvider(
            providers.anthropic.api_key.get_secret_value() if providers.anthropic.api_key else "",
            providers.anthropic.cost_per_unit_usd,
        )
    if providers.gemini.is_configured:
        registries.llm["gemini"] = GeminiProvider(
            providers.gemini.api_key.get_secret_value() if providers.gemini.api_key else "",
            providers.gemini.cost_per_unit_usd,
        )
    if providers.ollama.is_configured and providers.ollama.base_url:
        registries.llm["ollama"] = OllamaProvider(providers.ollama.base_url)
    if providers.lmstudio.is_configured and providers.lmstudio.base_url:
        registries.llm["lmstudio"] = LMStudioProvider(providers.lmstudio.base_url)

    if providers.flux_api.is_configured:
        registries.image["flux_api"] = FluxApiProvider(
            providers.flux_api.api_key.get_secret_value() if providers.flux_api.api_key else "",
            storage,
            raw_assets_bucket,
            providers.flux_api.cost_per_unit_usd,
        )
    if providers.sdxl_diffusers.is_configured and providers.sdxl_diffusers.base_url:
        registries.image["sdxl_diffusers"] = SdxlDiffusersProvider(
            providers.sdxl_diffusers.base_url, storage, raw_assets_bucket
        )
    if providers.comfyui.is_configured and providers.comfyui.base_url:
        registries.image["comfyui"] = ComfyUIProvider(providers.comfyui.base_url, storage, raw_assets_bucket)
    if providers.a1111.is_configured and providers.a1111.base_url:
        registries.image["a1111"] = A1111Provider(providers.a1111.base_url, storage, raw_assets_bucket)

    if providers.veo.is_configured:
        registries.video["veo"] = VeoProvider(
            providers.veo.api_key.get_secret_value() if providers.veo.api_key else "",
            storage,
            raw_assets_bucket,
            providers.veo.cost_per_unit_usd,
        )
    if providers.runway.is_configured:
        registries.video["runway"] = RunwayProvider(
            providers.runway.api_key.get_secret_value() if providers.runway.api_key else "",
            storage,
            raw_assets_bucket,
            providers.runway.cost_per_unit_usd,
        )
    if providers.kling.is_configured:
        registries.video["kling"] = KlingProvider(
            providers.kling.api_key.get_secret_value() if providers.kling.api_key else "",
            storage,
            raw_assets_bucket,
            providers.kling.cost_per_unit_usd,
        )
    if providers.luma.is_configured:
        registries.video["luma"] = LumaProvider(
            providers.luma.api_key.get_secret_value() if providers.luma.api_key else "",
            storage,
            raw_assets_bucket,
            providers.luma.cost_per_unit_usd,
        )
    if providers.hailuo.is_configured:
        registries.video["hailuo"] = HailuoProvider(
            providers.hailuo.api_key.get_secret_value() if providers.hailuo.api_key else "",
            storage,
            raw_assets_bucket,
            providers.hailuo.cost_per_unit_usd,
        )

    if providers.elevenlabs.is_configured:
        registries.tts["elevenlabs"] = ElevenLabsProvider(
            providers.elevenlabs.api_key.get_secret_value() if providers.elevenlabs.api_key else "",
            storage,
            raw_assets_bucket,
            providers.elevenlabs.cost_per_unit_usd,
        )
    if providers.playht.is_configured and providers.playht.api_key:
        registries.tts["playht"] = PlayHTProvider(
            providers.playht.api_key.get_secret_value(), "", storage, raw_assets_bucket, providers.playht.cost_per_unit_usd
        )
    if providers.azure_tts.is_configured and providers.azure_tts.api_key:
        registries.tts["azure_tts"] = AzureTtsProvider(
            providers.azure_tts.api_key.get_secret_value(),
            "eastus",
            storage,
            raw_assets_bucket,
            providers.azure_tts.cost_per_unit_usd,
        )
    if providers.kokoro.is_configured and providers.kokoro.base_url:
        registries.tts["kokoro"] = KokoroProvider(providers.kokoro.base_url, storage, raw_assets_bucket)
    if providers.piper.is_configured and providers.piper.base_url:
        registries.tts["piper"] = PiperProvider(providers.piper.base_url, storage, raw_assets_bucket)

    if providers.suno.is_configured:
        registries.music["suno"] = SunoProvider(
            providers.suno.api_key.get_secret_value() if providers.suno.api_key else "",
            storage,
            raw_assets_bucket,
            providers.suno.cost_per_unit_usd,
        )
    if providers.udio.is_configured:
        registries.music["udio"] = UdioProvider(
            providers.udio.api_key.get_secret_value() if providers.udio.api_key else "",
            storage,
            raw_assets_bucket,
            providers.udio.cost_per_unit_usd,
        )
    if providers.mubert.is_configured:
        registries.music["mubert"] = MubertProvider(
            providers.mubert.api_key.get_secret_value() if providers.mubert.api_key else "",
            storage,
            raw_assets_bucket,
            providers.mubert.cost_per_unit_usd,
        )

    return registries
