from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True, slots=True)
class TTSRequest:
    text: str
    model: str
    voice_id: str
    metadata: dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class WordTimestamp:
    word: str
    start: float
    end: float


@dataclass(frozen=True, slots=True)
class AudioAsset:
    object_key: str
    content_type: str
    duration_seconds: float
    model: str
    latency_ms: int
    word_timestamps: list[WordTimestamp] = field(default_factory=list)
    cost_usd: float | None = None


@dataclass(frozen=True, slots=True)
class VoiceCloneRequest:
    """Approval-gated (ARCHITECTURE.md §8) — callers must hold a granted
    VOICE_CLONING approval before invoking `TTSProvider.clone_voice`."""

    name: str
    sample_object_keys: list[str]
    consent_artifact_object_key: str


@dataclass(frozen=True, slots=True)
class ClonedVoice:
    provider_voice_id: str
    model: str
