from __future__ import annotations

import os
import re
from functools import lru_cache
from pathlib import Path
from typing import Any, Literal, cast
from urllib.parse import quote_plus

import yaml
from dotenv import load_dotenv
from pydantic import BaseModel, SecretStr
from pydantic_settings import BaseSettings, PydanticBaseSettingsSource, SettingsConfigDict

CONFIG_DIR = Path(__file__).resolve().parents[5] / "config"
REPO_ROOT = CONFIG_DIR.parent
_ENV_VAR_PATTERN = re.compile(r"\$\{([A-Za-z_][A-Za-z0-9_]*)\}")


class AppSettings(BaseModel):
    name: str = "ytforge"
    env: Literal["development", "staging", "production"] = "development"
    debug: bool = False
    cors_origins: list[str] = []


class SecuritySettings(BaseModel):
    jwt_secret: SecretStr
    access_token_ttl_minutes: int = 15
    refresh_token_ttl_days: int = 14
    # KEK (key-encryption-key) for envelope-encrypting channel OAuth refresh
    # tokens (ARCHITECTURE.md §8) — base64-encoded 32 bytes, required like
    # jwt_secret (no safe default for a key that decrypts stored secrets).
    encryption_master_key: SecretStr


class ModelRoute(BaseModel):
    primary: str
    fallback: list[str] = []


class DiscoveryEndpoint(BaseModel):
    base_url: str
    auto_detect: bool = True


class QdrantSettings(BaseModel):
    url: str = "http://localhost:6333"


class TemporalSettings(BaseModel):
    host: str = "localhost:7233"
    namespace: str = "default"
    task_queue: str = "ytforge-pipeline"
    # Separate queue for the FFmpeg-heavy renderer pool (ARCHITECTURE.md
    # §1: "same codebase as worker but a separate task queue and container
    # ... so CPU/GPU-heavy rendering scales independently of I/O-bound
    # agents"). Only the `editing` agent's activity call routes here —
    # see VideoProductionWorkflow.
    renderer_task_queue: str = "ytforge-renderer"


class RedisSettings(BaseModel):
    url: str = "redis://localhost:6379/0"
    events_stream: str = "events"
    events_dlq_stream: str = "events:dlq"
    consumer_group: str = "ytforge-consumers"


class MinioSettings(BaseModel):
    endpoint: str = "localhost:9000"
    access_key: str = "minioadmin"
    secret_key: SecretStr = SecretStr("minioadmin")
    secure: bool = False
    buckets: dict[str, str] = {
        "raw_assets": "raw-assets",
        "renders": "renders",
        "thumbnails": "thumbnails",
        "voices": "voices",
        "exports": "exports",
    }


class ModelsSettings(BaseModel):
    # "fake" selects infrastructure/providers/fakeprovider/ for every route,
    # regardless of what's configured below — the only way to exercise the
    # 12 agents without any real provider credentials or local model server.
    provider_set: Literal["real", "fake"] = "real"
    routes: dict[str, ModelRoute] = {}
    discovery: dict[str, DiscoveryEndpoint] = {}


class GoogleOAuthSettings(BaseModel):
    client_id: str = ""
    client_secret: SecretStr = SecretStr("")
    redirect_uri: str = "http://localhost:8000/api/v1/auth/google/callback"


class YouTubeSettings(BaseModel):
    upload_quota_cost: int = 1600
    daily_quota_budget: int = 10000


class ObservabilitySettings(BaseModel):
    # Empty = disabled — no OTel Collector runs by default outside the
    # `observability` compose profile (Phase 9), so instrumentation must
    # no-op cleanly rather than fail app startup when this is unset.
    otel_exporter_endpoint: str = ""
    service_name: str = "ytforge"


class ProviderSettings(BaseModel):
    api_key: SecretStr | None = None
    base_url: str | None = None
    rate_limit_per_minute: int | None = None
    # meaning of "unit" varies by provider (per 1K tokens, per image, per
    # second of audio/video, …) — adapters interpret it, this is just the
    # configured rate.
    cost_per_unit_usd: float | None = None

    @property
    def is_configured(self) -> bool:
        """True once either a real key or a reachable base_url is set —
        used to decide whether ModelRouter/discovery should register this
        provider at all."""
        has_key = self.api_key is not None and self.api_key.get_secret_value() != ""
        has_url = self.base_url is not None and self.base_url != ""
        return has_key or has_url


class ProvidersSettings(BaseModel):
    openai: ProviderSettings = ProviderSettings()
    anthropic: ProviderSettings = ProviderSettings()
    gemini: ProviderSettings = ProviderSettings()
    groq: ProviderSettings = ProviderSettings()
    ollama: ProviderSettings = ProviderSettings()
    lmstudio: ProviderSettings = ProviderSettings()
    flux_api: ProviderSettings = ProviderSettings()
    pollinations: ProviderSettings = ProviderSettings()
    sdxl_diffusers: ProviderSettings = ProviderSettings()
    comfyui: ProviderSettings = ProviderSettings()
    a1111: ProviderSettings = ProviderSettings()
    veo: ProviderSettings = ProviderSettings()
    runway: ProviderSettings = ProviderSettings()
    kling: ProviderSettings = ProviderSettings()
    luma: ProviderSettings = ProviderSettings()
    hailuo: ProviderSettings = ProviderSettings()
    elevenlabs: ProviderSettings = ProviderSettings()
    playht: ProviderSettings = ProviderSettings()
    azure_tts: ProviderSettings = ProviderSettings()
    kokoro: ProviderSettings = ProviderSettings()
    piper: ProviderSettings = ProviderSettings()
    suno: ProviderSettings = ProviderSettings()
    udio: ProviderSettings = ProviderSettings()
    mubert: ProviderSettings = ProviderSettings()


class DatabaseSettings(BaseModel):
    host: str
    port: int = 5432
    user: str
    password: SecretStr
    name: str
    pool_size: int = 10
    echo: bool = False

    @property
    def dsn(self) -> str:
        return (
            f"postgresql+asyncpg://{quote_plus(self.user)}:"
            f"{quote_plus(self.password.get_secret_value())}@{self.host}:{self.port}/{self.name}"
        )


def _expand_env_vars(value: Any) -> Any:
    if isinstance(value, str):
        return _ENV_VAR_PATTERN.sub(lambda m: os.environ.get(m.group(1), ""), value)
    if isinstance(value, dict):
        return {k: _expand_env_vars(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_expand_env_vars(v) for v in value]
    return value


def _deep_merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    merged = dict(base)
    for key, value in override.items():
        if key in merged and isinstance(merged[key], dict) and isinstance(value, dict):
            merged[key] = _deep_merge(merged[key], value)
        else:
            merged[key] = value
    return merged


def _load_yaml(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as fh:
        loaded: dict[str, Any] | None = yaml.safe_load(fh)
    return loaded or {}


def _load_merged_yaml(config_dir: Path = CONFIG_DIR) -> dict[str, Any]:
    env_name = os.environ.get("YTFORGE_APP_ENV", "development")
    merged = _load_yaml(config_dir / "default.yaml")
    merged = _deep_merge(merged, _load_yaml(config_dir / f"{env_name}.yaml"))
    merged.setdefault("app", {})["env"] = env_name
    return cast("dict[str, Any]", _expand_env_vars(merged))


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="YTFORGE__",
        env_nested_delimiter="__",
        extra="ignore",
    )

    app: AppSettings
    database: DatabaseSettings
    security: SecuritySettings
    models: ModelsSettings = ModelsSettings()
    providers: ProvidersSettings = ProvidersSettings()
    qdrant: QdrantSettings = QdrantSettings()
    temporal: TemporalSettings = TemporalSettings()
    redis: RedisSettings = RedisSettings()
    minio: MinioSettings = MinioSettings()
    google_oauth: GoogleOAuthSettings = GoogleOAuthSettings()
    youtube: YouTubeSettings = YouTubeSettings()
    observability: ObservabilitySettings = ObservabilitySettings()

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> tuple[PydanticBaseSettingsSource, ...]:
        # env vars must win over YAML (which arrives via init kwargs below).
        return (env_settings, init_settings, dotenv_settings, file_secret_settings)


@lru_cache
def get_settings() -> Settings:
    # Populates os.environ from the repo-root .env for local (non-Docker)
    # runs, where nothing else sources it — Docker Compose's own env_file:
    # directive already does this inside containers, and override=False
    # means a real environment variable set there (or by CI) always wins
    # over the .env file's value.
    load_dotenv(REPO_ROOT / ".env", override=False)
    return Settings(**_load_merged_yaml())
