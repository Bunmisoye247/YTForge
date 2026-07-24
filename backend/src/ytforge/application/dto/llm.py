from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True, slots=True)
class LLMMessage:
    role: str  # "system" | "user" | "assistant"
    content: str


@dataclass(frozen=True, slots=True)
class LLMRequest:
    model: str
    messages: list[LLMMessage]
    temperature: float = 0.7
    max_tokens: int | None = None
    metadata: dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class LLMResponse:
    content: str
    model: str
    input_tokens: int
    output_tokens: int
    latency_ms: int
    cost_usd: float | None = None


@dataclass(frozen=True, slots=True)
class LLMChunk:
    delta: str
    is_final: bool = False
