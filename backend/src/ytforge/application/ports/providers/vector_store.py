from __future__ import annotations

from typing import Protocol

from ytforge.application.dto.vector import Vector, VectorMatch, VectorPoint


class VectorStore(Protocol):
    async def upsert(self, collection: str, points: list[VectorPoint]) -> None: ...
    async def query(
        self, collection: str, vector: Vector, limit: int = 10
    ) -> list[VectorMatch]: ...
    async def delete(self, collection: str, point_ids: list[str]) -> None: ...
