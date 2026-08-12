# syntax=docker/dockerfile:1
# Multi-stage build for the `api`, `worker`, and `outbox-relay` deployable
# units (ARCHITECTURE.md §1/§13) — all three run this same lean image with
# different `command:` overrides in compose. The FFmpeg-heavy `renderer`
# unit uses Dockerfile.renderer instead (same builder stage, extra system
# packages in its runtime stage).
#
# Build context is the repo root (`docker build -f backend/Dockerfile .`)
# so this can COPY `config/` and `backend/prompts/` alongside the app.

FROM python:3.12-slim AS builder

COPY --from=ghcr.io/astral-sh/uv:0.5 /uv /uvx /bin/

WORKDIR /app/backend
ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=never

# Dependencies first (cached separately from app code) — installing before
# copying source means a source-only change doesn't invalidate this layer.
COPY backend/pyproject.toml backend/uv.lock ./
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-install-project --no-dev

COPY backend/ ./
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev

FROM python:3.12-slim AS runtime

RUN groupadd --system ytforge && useradd --system --gid ytforge --create-home --home-dir /app ytforge

WORKDIR /app
COPY --from=builder --chown=ytforge:ytforge /app/backend /app/backend
COPY --chown=ytforge:ytforge config /app/config

ENV PATH="/app/backend/.venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    YTFORGE_APP_ENV=production

WORKDIR /app/backend
USER ytforge

ENTRYPOINT ["ytforge"]
CMD ["serve", "--host", "0.0.0.0", "--port", "8000"]
