from __future__ import annotations

import uuid
from dataclasses import dataclass

from ytforge.domain.enums import ProjectStatus


@dataclass(frozen=True, slots=True)
class ProjectStatusChanged:
    project_id: uuid.UUID
    from_status: ProjectStatus
    to_status: ProjectStatus
