from __future__ import annotations

from pathlib import Path

from alembic import command
from alembic.config import Config

_ALEMBIC_INI = Path(__file__).resolve().parents[4] / "alembic.ini"


def migrate() -> None:
    """Thin wrapper around `alembic upgrade head` so container entrypoints
    (`deploy/docker/`) can run `ytforge migrate` instead of needing the
    `alembic` CLI + working directory set up separately — the DB URL still
    resolves the same way (`migrations/env.py` calls `get_settings()`.
    database.dsn`, unaffected by running from a different cwd)."""
    config = Config(str(_ALEMBIC_INI))
    command.upgrade(config, "head")
