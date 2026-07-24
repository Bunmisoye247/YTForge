from __future__ import annotations

from ytforge.domain.errors import InvalidTransitionError


class ApplicationError(Exception):
    """Base class for all use-case-level failures. Mapped to RFC 7807
    problem+json responses by the interfaces-layer exception handlers."""


class NotFoundError(ApplicationError):
    def __init__(self, entity: str, entity_id: object) -> None:
        self.entity = entity
        self.entity_id = entity_id
        super().__init__(f"{entity} {entity_id!r} not found")


class ConflictError(ApplicationError):
    pass


class InvalidStateError(ApplicationError):
    """Raised when a use case attempts an illegal domain state transition."""

    def __init__(self, cause: InvalidTransitionError) -> None:
        self.cause = cause
        super().__init__(str(cause))


class AuthenticationError(ApplicationError):
    pass


class AuthorizationError(ApplicationError):
    pass
