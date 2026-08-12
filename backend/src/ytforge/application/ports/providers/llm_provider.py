from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Protocol

from ytforge.application.dto.llm import LLMChunk, LLMRequest, LLMResponse
from ytforge.application.dto.vector import Vector


class LLMProvider(Protocol):
    async def complete(self, req: LLMRequest) -> LLMResponse: ...
    def stream(self, req: LLMRequest) -> AsyncIterator[LLMChunk]: ...
    async def embed(self, texts: list[str], model: str) -> list[Vector]: ...
    async def health_check(self) -> None: ...
