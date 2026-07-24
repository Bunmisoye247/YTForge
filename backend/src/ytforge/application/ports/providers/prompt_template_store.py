from __future__ import annotations

from typing import Any, Protocol

from ytforge.application.dto.prompt import RenderedPrompt


class PromptTemplateStore(Protocol):
    def render(self, agent: str, name: str, variables: dict[str, Any]) -> RenderedPrompt: ...
