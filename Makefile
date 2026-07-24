.PHONY: dev test lint up down down-clean logs

# Local dev (no Docker) — matches CLAUDE.md's documented backend/frontend
# commands, just collected in one place.
dev:
	cd backend && uv run ytforge serve &
	cd frontend && npm run dev

test:
	cd backend && uv run pytest
	cd frontend && npm run test

lint:
	cd backend && uv run ruff check src tests && uv run mypy src && uv run lint-imports
	cd frontend && npm run lint && npm run typecheck

# Docker Compose — core profile is the minimal viable stack; add more via
# COMPOSE_PROFILES, e.g. `make up COMPOSE_PROFILES=core,observability,dev`.
COMPOSE_PROFILES ?= core
COMPOSE = docker compose -f deploy/compose/docker-compose.yml $(foreach p,$(subst $(comma),$(space),$(COMPOSE_PROFILES)),--profile $(p))
comma := ,
space := $(subst ,, )

up:
	$(COMPOSE) up -d

down:
	$(COMPOSE) down

down-clean:
	$(COMPOSE) down -v

logs:
	$(COMPOSE) logs -f
