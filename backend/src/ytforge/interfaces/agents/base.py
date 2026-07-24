from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Protocol

if TYPE_CHECKING:
    from ytforge.interfaces.agents.context import AgentContext


@dataclass(frozen=True, slots=True)
class AgentTask:
    project_id: uuid.UUID
    payload: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class AgentResult:
    ok: bool
    output: dict[str, Any] = field(default_factory=dict)
    error: str | None = None

    @classmethod
    def success(cls, **output: Any) -> AgentResult:
        return cls(ok=True, output=output)

    @classmethod
    def failure(cls, error: str) -> AgentResult:
        return cls(ok=False, error=error)


class Agent(Protocol):
    """ARCHITECTURE.md §3. Runs today via `ytforge run-agent` (manual CLI
    invocation); Phase 7 wraps the same classes in real Temporal
    activities without changing this shape — activities supply retries/
    timeouts/heartbeating "for free", agents don't reimplement any of it."""

    name: str

    async def run(self, task: AgentTask, ctx: AgentContext) -> AgentResult: ...
