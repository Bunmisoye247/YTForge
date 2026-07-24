from __future__ import annotations


class DomainError(Exception):
    """Base class for invariant violations raised by domain entities."""


class InvalidTransitionError(DomainError):
    def __init__(self, entity: str, from_state: str, to_state: str) -> None:
        self.entity = entity
        self.from_state = from_state
        self.to_state = to_state
        super().__init__(f"{entity} cannot transition from {from_state!r} to {to_state!r}")
