from __future__ import annotations

from uuid6 import uuid7

from ytforge.application.dto.vector import VectorPoint
from ytforge.application.use_cases.research import AddResearchDocumentInput, add_research_document
from ytforge.interfaces.agents.base import AgentResult, AgentTask
from ytforge.interfaces.agents.context import AgentContext
from ytforge.interfaces.agents.support import run_llm_step

_QDRANT_COLLECTION = "research"


class ResearchAgent:
    """Consumes a topic, produces research documents + Qdrant chunks
    (ARCHITECTURE.md §3). `task.payload["topic"]` is required."""

    name = "research"

    async def run(self, task: AgentTask, ctx: AgentContext) -> AgentResult:
        topic = task.payload.get("topic")
        if not topic:
            return AgentResult.failure("research agent requires payload['topic']")

        search_results = await ctx.tools.get("web_search").run(query=topic, max_results=5)
        sources_text = "\n".join(f"- {r.title} ({r.url}): {r.snippet}" for r in search_results)

        _rendered, response = await run_llm_step(
            ctx,
            agent="research",
            template_name="summarize",
            route_name="research_summary",
            variables={"topic": topic, "sources": sources_text},
            project_id=task.project_id,
        )

        primary_source = search_results[0] if search_results else None
        document = await add_research_document(
            ctx.uow,
            AddResearchDocumentInput(
                project_id=task.project_id,
                source_url=primary_source.url if primary_source else "https://example.com/no-source",
                title=f"Research summary: {topic}",
                content=response.content,
                citation={"sources": [r.url for r in search_results]},
            ),
        )

        vectors = await ctx.model_router.embed("embeddings", [response.content])
        await ctx.vector_store.upsert(
            _QDRANT_COLLECTION,
            [
                VectorPoint(
                    id=str(uuid7()),
                    vector=vectors[0],
                    payload={
                        "project_id": str(task.project_id),
                        "document_id": str(document.id),
                        "source_url": document.source_url,
                    },
                )
            ],
        )

        return AgentResult.success(research_document_id=str(document.id))
