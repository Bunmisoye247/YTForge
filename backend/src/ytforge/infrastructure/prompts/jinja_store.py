from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml
from jinja2 import Environment, StrictUndefined

from ytforge.application.common.errors import NotFoundError
from ytforge.application.dto.prompt import RenderedPrompt

_FILENAME_PATTERN = re.compile(r"^(?P<name>.+)\.v(?P<version>\d+)\.md\.j2$")
_FRONT_MATTER_PATTERN = re.compile(r"\A---\n(?P<front_matter>.*?)\n---\n(?P<body>.*)\Z", re.DOTALL)


@dataclass(frozen=True, slots=True)
class TemplateFile:
    path: Path
    agent: str
    name: str
    version: int


def _parse_filename(path: Path) -> TemplateFile | None:
    match = _FILENAME_PATTERN.match(path.name)
    if match is None:
        return None
    return TemplateFile(
        path=path, agent=path.parent.name, name=match.group("name"), version=int(match.group("version"))
    )


def _parse_front_matter(raw: str) -> tuple[dict[str, Any], str]:
    match = _FRONT_MATTER_PATTERN.match(raw)
    if match is None:
        raise ValueError("prompt template is missing a YAML front-matter block (--- ... ---)")
    front_matter = yaml.safe_load(match.group("front_matter")) or {}
    return front_matter, match.group("body")


class FilesystemPromptStore:
    """Loads `backend/prompts/{agent}/{name}.v{N}.md.j2` — disk is the
    source of truth (CLAUDE.md conventions: "never edit a version in place
    — create v{N+1}"); `ytforge sync-prompts` mirrors what's on disk into
    `prompt_templates`/`prompt_versions` for the dashboard, but rendering
    always reads from here directly."""

    def __init__(self, prompts_dir: Path) -> None:
        self._prompts_dir = prompts_dir
        self._env = Environment(undefined=StrictUndefined, autoescape=False)  # noqa: S701 - not HTML

    def latest_version_path(self, agent: str, name: str) -> Path:
        agent_dir = self._prompts_dir / agent
        candidates = [
            parsed
            for f in agent_dir.glob(f"{name}.v*.md.j2")
            if (parsed := _parse_filename(f)) is not None
        ]
        if not candidates:
            raise NotFoundError("PromptTemplate", f"{agent}/{name}")
        best = max(candidates, key=lambda c: c.version)
        return best.path

    def render(self, agent: str, name: str, variables: dict[str, Any]) -> RenderedPrompt:
        path = self.latest_version_path(agent, name)
        parsed = _parse_filename(path)
        assert parsed is not None
        raw = path.read_text(encoding="utf-8")
        front_matter, body = _parse_front_matter(raw)

        template = self._env.from_string(body)
        content = template.render(**variables)

        return RenderedPrompt(
            content=content,
            agent=agent,
            name=name,
            version=parsed.version,
            model_hints=front_matter.get("model_hints", {}),
            variables_used=variables,
        )

    def list_all_versions(self) -> list[TemplateFile]:
        """Used by `ytforge sync-prompts` — every version file on disk,
        not just the latest, so history stays visible in the dashboard."""
        results: list[TemplateFile] = []
        if not self._prompts_dir.exists():
            return results
        for agent_dir in sorted(self._prompts_dir.iterdir()):
            if not agent_dir.is_dir():
                continue
            for f in sorted(agent_dir.glob("*.v*.md.j2")):
                parsed = _parse_filename(f)
                if parsed is not None:
                    results.append(parsed)
        return results

    def read_front_matter_and_body(self, path: Path) -> tuple[dict[str, Any], str]:
        return _parse_front_matter(path.read_text(encoding="utf-8"))
