from __future__ import annotations

import asyncio

import typer
import uvicorn

from ytforge.infrastructure.config.settings import get_settings
from ytforge.interfaces.cli.detect_models import detect_models as detect_models_impl
from ytforge.interfaces.cli.migrate import migrate as migrate_impl
from ytforge.interfaces.cli.replay_dlq import discard_dlq_entry, list_dlq, replay_dlq_entry
from ytforge.interfaces.cli.run_agent import run_agent as run_agent_impl
from ytforge.interfaces.cli.run_relay import run_relay as run_relay_impl
from ytforge.interfaces.cli.run_renderer import run_renderer as run_renderer_impl
from ytforge.interfaces.cli.run_worker import run_worker as run_worker_impl
from ytforge.interfaces.cli.seed import seed as run_seed
from ytforge.interfaces.cli.start_pipeline import start_pipeline as start_pipeline_impl
from ytforge.interfaces.cli.sync_prompts import sync_prompts as run_sync_prompts

app = typer.Typer(name="ytforge", help="YTForge operational CLI.")


@app.command()
def seed() -> None:
    """Populate the database with a representative sample pipeline for local development."""
    asyncio.run(run_seed())


@app.command(name="sync-prompts")
def sync_prompts() -> None:
    """Mirror backend/prompts/**/*.v{N}.md.j2 into prompt_templates/prompt_versions."""
    asyncio.run(run_sync_prompts())


@app.command(name="run-agent")
def run_agent(
    agent_name: str = typer.Argument(..., help="One of: " + ", ".join(sorted(
        ["trend", "research", "writer", "fact_checker", "storyboard", "image", "video", "voice",
         "editing", "seo", "publisher", "analytics"]
    ))),
    project_id: str = typer.Option(..., "--project-id", help="UUID of the project to run against."),
    payload: str = typer.Option("{}", "--payload", help="JSON-encoded agent task payload."),
) -> None:
    """Manually invoke one agent — the Phase-6 invocation path until Phase
    7 wraps these same agent classes in Temporal activities. Set
    YTFORGE__MODELS__PROVIDER_SET=fake to run without any real provider
    credentials."""
    asyncio.run(run_agent_impl(agent_name, project_id, payload))


@app.command(name="run-worker")
def run_worker() -> None:
    """Run the Temporal worker (workflows + agent activities) — the
    `worker` deployable unit (ARCHITECTURE.md §1/§13). Requires a reachable
    Temporal server (`YTFORGE__TEMPORAL__HOST`, default localhost:7233).
    Rendering and outbox relay are separate: `run-renderer`/`run-relay`."""
    asyncio.run(run_worker_impl())


@app.command(name="run-renderer")
def run_renderer() -> None:
    """Run the Temporal renderer worker — the `renderer` deployable unit
    (ARCHITECTURE.md §1/§13), listening on a dedicated task queue for the
    FFmpeg-heavy `editing` agent step so it scales independently of the
    main worker. Same activity code as `run-worker`, different queue."""
    asyncio.run(run_renderer_impl())


@app.command(name="run-relay")
def run_relay() -> None:
    """Run the outbox-relay loop — the `outbox-relay` deployable unit
    (ARCHITECTURE.md §13's `core` compose profile). Polls the
    transactional outbox and republishes to Redis Streams."""
    asyncio.run(run_relay_impl())


@app.command(name="migrate")
def migrate() -> None:
    """Run `alembic upgrade head` — the container-entrypoint-friendly
    equivalent of the raw alembic CLI."""
    migrate_impl()


@app.command(name="detect-models")
def detect_models() -> None:
    """Scan configured local model-server endpoints (Ollama, LM Studio,
    ComfyUI) and register what's found in `model_registry`."""
    asyncio.run(detect_models_impl())


@app.command(name="start-pipeline")
def start_pipeline(
    project_id: str = typer.Option(..., "--project-id", help="UUID of the project to run the pipeline for."),
    topic: str = typer.Option(..., "--topic", help="Video topic (fed to Research/Writer agents)."),
    requested_by_user_id: str = typer.Option(..., "--user-id", help="UUID attributed as the approval requester."),
) -> None:
    """Starts a `VideoProductionWorkflow` run against a real Temporal
    server — the manual invocation path for the full pipeline, same role
    `run-agent` plays for a single agent."""
    asyncio.run(start_pipeline_impl(project_id, topic, requested_by_user_id))


@app.command(name="replay-dlq")
def replay_dlq(
    replay: str = typer.Option(None, "--replay", help="Message id to replay back onto the main events stream."),
    discard: str = typer.Option(None, "--discard", help="Message id to discard from the DLQ."),
) -> None:
    """Inspect/replay/discard `events:dlq` entries — the CLI stand-in for
    the operator UI ARCHITECTURE.md §5.3 calls for. With no options, lists
    every DLQ entry."""
    if replay and discard:
        print("Pass only one of --replay or --discard.")
        raise SystemExit(1)
    if replay:
        asyncio.run(replay_dlq_entry(replay))
    elif discard:
        asyncio.run(discard_dlq_entry(discard))
    else:
        asyncio.run(list_dlq())


@app.command()
def serve(host: str = "127.0.0.1", port: int = 8000) -> None:
    """Run the FastAPI app with uvicorn for local development."""
    settings = get_settings()
    uvicorn.run(
        "ytforge.interfaces.api.main:create_app",
        factory=True,
        host=host,
        port=port,
        reload=settings.app.debug,
    )


if __name__ == "__main__":
    app()
