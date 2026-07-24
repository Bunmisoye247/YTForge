from __future__ import annotations

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse

from ytforge.application.common.errors import (
    ApplicationError,
    AuthenticationError,
    AuthorizationError,
    ConflictError,
    InvalidStateError,
    NotFoundError,
)

_STATUS_BY_ERROR: dict[type[ApplicationError], int] = {
    NotFoundError: status.HTTP_404_NOT_FOUND,
    ConflictError: status.HTTP_409_CONFLICT,
    InvalidStateError: status.HTTP_409_CONFLICT,
    AuthenticationError: status.HTTP_401_UNAUTHORIZED,
    AuthorizationError: status.HTTP_403_FORBIDDEN,
}


def _problem_response(status_code: int, title: str, detail: str) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content={"type": "about:blank", "title": title, "status": status_code, "detail": detail},
        media_type="application/problem+json",
    )


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(ApplicationError)
    async def _application_error_handler(request: Request, exc: ApplicationError) -> JSONResponse:
        status_code = _STATUS_BY_ERROR.get(type(exc), status.HTTP_400_BAD_REQUEST)
        return _problem_response(status_code, type(exc).__name__, str(exc))

    @app.exception_handler(Exception)
    async def _unhandled_error_handler(request: Request, exc: Exception) -> JSONResponse:
        return _problem_response(
            status.HTTP_500_INTERNAL_SERVER_ERROR, "InternalServerError", "an unexpected error occurred"
        )
