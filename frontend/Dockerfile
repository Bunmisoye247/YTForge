# syntax=docker/dockerfile:1
# The `web` deployable unit (ARCHITECTURE.md §1/§13). Build context is the
# repo root (`docker build -f frontend/Dockerfile .`). Three stages: deps
# (cached node_modules), build (next build, standalone output), runtime
# (just the standalone bundle — no full node_modules, no dev deps).

FROM node:22-slim AS deps
WORKDIR /app
COPY frontend/package.json frontend/package-lock.json ./
RUN --mount=type=cache,target=/root/.npm \
    npm ci

FROM node:22-slim AS build
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY frontend/ ./
ARG NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
ENV NEXT_PUBLIC_API_BASE_URL=${NEXT_PUBLIC_API_BASE_URL}
RUN npm run build

FROM node:22-slim AS runtime
RUN groupadd --system ytforge && useradd --system --gid ytforge --create-home --home-dir /app ytforge

# CMD is a plain `node server.js` (Next's standalone output bundles its own
# runtime deps) — npm/npx/corepack are never invoked here, so strip them
# rather than ship whatever CVEs happen to be in npm's own vendored deps
# (tar, sigstore, etc.) at this base image's current patch level.
RUN rm -rf /usr/local/lib/node_modules/npm /usr/local/lib/node_modules/corepack \
    /usr/local/bin/npm /usr/local/bin/npx /usr/local/bin/corepack

WORKDIR /app

COPY --from=build --chown=ytforge:ytforge /app/public ./public
COPY --from=build --chown=ytforge:ytforge /app/.next/standalone ./
COPY --from=build --chown=ytforge:ytforge /app/.next/static ./.next/static

ENV NODE_ENV=production \
    PORT=3000 \
    HOSTNAME=0.0.0.0

USER ytforge
EXPOSE 3000

CMD ["node", "server.js"]
