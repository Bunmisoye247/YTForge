from __future__ import annotations

from pathlib import Path

import pytest
from jinja2.exceptions import UndefinedError

from ytforge.application.common.errors import NotFoundError
from ytforge.infrastructure.prompts.jinja_store import FilesystemPromptStore


def _write_template(prompts_dir: Path, agent: str, name: str, version: int, front_matter: str, body: str) -> Path:
    agent_dir = prompts_dir / agent
    agent_dir.mkdir(parents=True, exist_ok=True)
    path = agent_dir / f"{name}.v{version}.md.j2"
    path.write_text(f"---\n{front_matter}\n---\n{body}", encoding="utf-8")
    return path


def test_render_picks_highest_version(tmp_path: Path) -> None:
    _write_template(tmp_path, "writer", "video_script", 1, "version: 1\nmodel_hints: {}\n", "v1 body: {{ topic }}")
    _write_template(tmp_path, "writer", "video_script", 2, "version: 2\nmodel_hints: {}\n", "v2 body: {{ topic }}")
    _write_template(tmp_path, "writer", "video_script", 10, "version: 10\nmodel_hints: {}\n", "v10 body: {{ topic }}")

    store = FilesystemPromptStore(tmp_path)
    rendered = store.render("writer", "video_script", {"topic": "cats"})

    assert rendered.version == 10
    assert rendered.content == "v10 body: cats"


def test_render_parses_front_matter_model_hints(tmp_path: Path) -> None:
    _write_template(
        tmp_path,
        "seo",
        "metadata",
        1,
        "version: 1\nmodel_hints:\n  temperature: 0.2\n  max_tokens: 500\n",
        "hello {{ name }}",
    )

    store = FilesystemPromptStore(tmp_path)
    rendered = store.render("seo", "metadata", {"name": "world"})

    assert rendered.model_hints == {"temperature": 0.2, "max_tokens": 500}
    assert rendered.agent == "seo"
    assert rendered.name == "metadata"
    assert rendered.variables_used == {"name": "world"}


def test_render_raises_not_found_for_missing_template(tmp_path: Path) -> None:
    store = FilesystemPromptStore(tmp_path)
    with pytest.raises(NotFoundError):
        store.render("nonexistent", "nope", {})


def test_render_raises_for_missing_variable(tmp_path: Path) -> None:
    _write_template(tmp_path, "writer", "video_script", 1, "version: 1\n", "{{ missing_var }}")
    store = FilesystemPromptStore(tmp_path)
    with pytest.raises(UndefinedError):
        store.render("writer", "video_script", {})


def test_list_all_versions_includes_every_version_not_just_latest(tmp_path: Path) -> None:
    _write_template(tmp_path, "writer", "video_script", 1, "version: 1\n", "body v1")
    _write_template(tmp_path, "writer", "video_script", 2, "version: 2\n", "body v2")
    _write_template(tmp_path, "seo", "metadata", 1, "version: 1\n", "body seo")

    store = FilesystemPromptStore(tmp_path)
    versions = store.list_all_versions()

    keys = {(v.agent, v.name, v.version) for v in versions}
    assert keys == {("writer", "video_script", 1), ("writer", "video_script", 2), ("seo", "metadata", 1)}


def test_list_all_versions_empty_when_dir_missing(tmp_path: Path) -> None:
    store = FilesystemPromptStore(tmp_path / "does-not-exist")
    assert store.list_all_versions() == []


def test_read_front_matter_and_body(tmp_path: Path) -> None:
    path = _write_template(tmp_path, "writer", "video_script", 1, "version: 1\nmodel_hints: {}\n", "the body text")
    store = FilesystemPromptStore(tmp_path)

    front_matter, body = store.read_front_matter_and_body(path)

    assert front_matter == {"version": 1, "model_hints": {}}
    assert body == "the body text"
