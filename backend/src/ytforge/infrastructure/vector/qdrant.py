from __future__ import annotations

from qdrant_client import AsyncQdrantClient
from qdrant_client.http import models as qmodels

from ytforge.application.dto.vector import Vector, VectorMatch, VectorPoint


class QdrantVectorStore:
    """Qdrant vector store adapter (ARCHITECTURE.md §6.2 — `research`,
    `performance_memory`, `script_library`, `trend_history` collections).
    Not exercised live here (no Qdrant instance running); verified via
    `infrastructure/vector/fake.py` in tests."""

    def __init__(self, url: str) -> None:
        self._client = AsyncQdrantClient(url=url)

    async def upsert(self, collection: str, points: list[VectorPoint]) -> None:
        await self._ensure_collection(collection, len(points[0].vector) if points else 0)
        await self._client.upsert(
            collection_name=collection,
            points=[
                qmodels.PointStruct(id=p.id, vector=p.vector, payload=p.payload) for p in points
            ],
        )

    async def query(self, collection: str, vector: Vector, limit: int = 10) -> list[VectorMatch]:
        response = await self._client.query_points(
            collection_name=collection, query=vector, limit=limit
        )
        return [
            VectorMatch(id=str(r.id), score=r.score, payload=r.payload or {}) for r in response.points
        ]

    async def delete(self, collection: str, point_ids: list[str]) -> None:
        await self._client.delete(
            collection_name=collection,
            points_selector=qmodels.PointIdsList(points=list(point_ids)),
        )

    async def _ensure_collection(self, collection: str, vector_size: int) -> None:
        if vector_size == 0 or await self._client.collection_exists(collection):
            return
        await self._client.create_collection(
            collection_name=collection,
            vectors_config=qmodels.VectorParams(size=vector_size, distance=qmodels.Distance.COSINE),
        )
