from __future__ import annotations

from pathlib import Path

from ytforge.infrastructure.config.settings import ModelRoute
from ytforge.infrastructure.external.youtube.fake import FakeYouTubeGateway
from ytforge.infrastructure.providers.fakeprovider import (
    FakeImageProvider,
    FakeLLMProvider,
    FakeMusicProvider,
    FakeSearchProvider,
    FakeTTSProvider,
    FakeVideoProvider,
)
from ytforge.infrastructure.providers.registry import ProviderRegistries
from ytforge.infrastructure.providers.router import ConfigDrivenModelRouter
from ytforge.infrastructure.rendering.fake import FakeEditingPipeline
from ytforge.infrastructure.storage.fake import FakeObjectStorage
from ytforge.infrastructure.vector.fake import FakeVectorStore
from ytforge.interfaces.agents.context import AgentContext
from ytforge.interfaces.agents.tools import (
    CalculatorTool,
    QdrantRetrievalTool,
    ToolRegistry,
    WebSearchTool,
    YouTubeLookupTool,
)

PROMPTS_DIR = Path(__file__).resolve().parents[2] / "prompts"

_TEST_ROUTES = {
    "script_writing": {"primary": "openai/gpt-4.1", "fallback": ["anthropic/claude-sonnet-4-6"]},
    "fact_checking": {"primary": "openai/gpt-4.1", "fallback": []},
    "research_summary": {"primary": "openai/gpt-4.1", "fallback": []},
    "storyboard": {"primary": "openai/gpt-4.1", "fallback": []},
    "seo": {"primary": "openai/gpt-4.1", "fallback": []},
    "trend_scoring": {"primary": "openai/gpt-4.1", "fallback": []},
    "voice_direction": {"primary": "openai/gpt-4.1", "fallback": []},
    "analytics_insights": {"primary": "openai/gpt-4.1", "fallback": []},
    "embeddings": {"primary": "openai/text-embedding-3-large", "fallback": []},
    "image_generation": {"primary": "flux_api/flux-pro-1.1", "fallback": []},
    "video_generation": {"primary": "runway/gen3", "fallback": []},
    "voice_synthesis": {"primary": "elevenlabs/eleven_multilingual_v2", "fallback": []},
    "music_generation": {"primary": "suno/v3", "fallback": []},
}


def make_fake_routes() -> dict[str, ModelRoute]:
    return {name: ModelRoute(**cfg) for name, cfg in _TEST_ROUTES.items()}


def make_fake_registries() -> ProviderRegistries:
    return ProviderRegistries(
        llm={name: FakeLLMProvider() for name in ("openai", "anthropic", "gemini", "ollama", "lmstudio")},
        image={name: FakeImageProvider() for name in ("flux_api", "sdxl_diffusers", "comfyui", "a1111")},
        video={name: FakeVideoProvider() for name in ("veo", "runway", "kling", "luma", "hailuo")},
        tts={name: FakeTTSProvider() for name in ("elevenlabs", "playht", "azure_tts", "kokoro", "piper")},
        music={name: FakeMusicProvider() for name in ("suno", "udio", "mubert")},
    )


def make_test_agent_context(uow: object, prompts: object) -> AgentContext:
    model_router = ConfigDrivenModelRouter(make_fake_routes(), make_fake_registries())
    vector_store = FakeVectorStore()
    tools = ToolRegistry(
        [
            CalculatorTool(),
            WebSearchTool(FakeSearchProvider()),
            QdrantRetrievalTool(vector_store),
            YouTubeLookupTool(),
        ]
    )
    return AgentContext(
        model_router=model_router,
        tools=tools,
        prompts=prompts,  # type: ignore[arg-type]
        uow=uow,  # type: ignore[arg-type]
        vector_store=vector_store,
        object_storage=FakeObjectStorage(),
        editing_pipeline=FakeEditingPipeline(),
        youtube_gateway=FakeYouTubeGateway(),
    )
