from __future__ import annotations


class ProviderError(Exception):
    """Base class for provider-adapter failures."""

    def __init__(self, provider: str, message: str) -> None:
        self.provider = provider
        super().__init__(f"{provider}: {message}")


class ProviderAuthError(ProviderError):
    """Missing or rejected credentials — never worth retrying/falling back
    without operator intervention, but ModelRouter still tries the next
    fallback since a different provider may have a valid key."""


class ProviderRateLimitError(ProviderError):
    pass


class ProviderRequestError(ProviderError):
    """Non-2xx response or malformed payload."""


class AllProvidersExhaustedError(Exception):
    """Raised by ModelRouter when the primary and every fallback in a
    route's chain failed."""

    def __init__(self, route_name: str, attempts: list[ProviderError]) -> None:
        self.route_name = route_name
        self.attempts = attempts
        detail = "; ".join(str(a) for a in attempts)
        super().__init__(f"route {route_name!r} exhausted all providers: {detail}")
