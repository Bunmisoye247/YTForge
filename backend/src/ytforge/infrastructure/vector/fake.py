from __future__ import annotations

import math

from ytforge.application.dto.vector import Vector, VectorMatch, VectorPoint


def _cosine_similarity(a: Vector, b: Vector) -> float:
    dot = sum(x * y for x, y in zip(a, b, strict=False))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(y * y for y in b))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


class FakeVectorStore:
    """In-memory `VectorStore` for tests — no Qdrant needed."""

    def __init__(self) -> None:
        self._collections: dict[str, dict[str, VectorPoint]] = {}

    async def upsert(self, collection: str, points: list[VectorPoint]) -> None:
        self._collections.setdefault(collection, {})
        for point in points:
            self._collections[collection][point.id] = point

    async def query(self, collection: str, vector: Vector, limit: int = 10) -> list[VectorMatch]:
        points = self._collections.get(collection, {})
        scored = [
            VectorMatch(id=p.id, score=_cosine_similarity(vector, p.vector), payload=p.payload)
            for p in points.values()
        ]
        scored.sort(key=lambda m: m.score, reverse=True)
        return scored[:limit]

    async def delete(self, collection: str, point_ids: list[str]) -> None:
        points = self._collections.get(collection, {})
        for point_id in point_ids:
            points.pop(point_id, None)
