from __future__ import annotations

import ast
import operator
from collections.abc import Callable
from typing import Any, Protocol

from ytforge.application.dto.search import SearchQuery, SearchResult
from ytforge.application.dto.vector import Vector, VectorMatch
from ytforge.application.ports.providers.search_provider import SearchProvider
from ytforge.application.ports.providers.vector_store import VectorStore


class Tool(Protocol):
    """A structural marker only — each concrete tool's `run()` has its own
    specific keyword signature (`expression=`, `query=`, `collection=`, …),
    so callers call `ctx.tools.get(name).run(...)` knowing that tool's
    actual signature; `ToolRegistry` is a by-name lookup, not something
    that can usefully type-check a uniform call shape across tools."""

    name: str
    description: str


_BinaryOp = Callable[[float, float], float]
_UnaryOp = Callable[[float], float]
_SAFE_BINARY_OPERATORS: dict[type, _BinaryOp] = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.Pow: operator.pow,
    ast.Mod: operator.mod,
}
_SAFE_UNARY_OPERATORS: dict[type, _UnaryOp] = {
    ast.USub: operator.neg,
    ast.UAdd: operator.pos,
}


def _eval_node(node: ast.AST) -> float:
    if isinstance(node, ast.Constant) and isinstance(node.value, int | float):
        return float(node.value)
    if isinstance(node, ast.BinOp) and type(node.op) in _SAFE_BINARY_OPERATORS:
        binary_op = _SAFE_BINARY_OPERATORS[type(node.op)]
        return binary_op(_eval_node(node.left), _eval_node(node.right))
    if isinstance(node, ast.UnaryOp) and type(node.op) in _SAFE_UNARY_OPERATORS:
        unary_op = _SAFE_UNARY_OPERATORS[type(node.op)]
        return unary_op(_eval_node(node.operand))
    raise ValueError(f"unsupported expression: {ast.dump(node)}")


class CalculatorTool:
    """Pure arithmetic — no external calls, so this is the one tool that's
    genuinely, fully real (not fake-backed) in this environment. Uses an
    `ast`-restricted evaluator rather than `eval()`, since the expression
    ultimately comes from LLM output."""

    name = "calculator"
    description = "Evaluates a basic arithmetic expression (+ - * / ** %)."

    async def run(self, expression: str) -> float:
        tree = ast.parse(expression, mode="eval")
        return _eval_node(tree.body)


class WebSearchTool:
    name = "web_search"
    description = "Searches the web for a query, returning the top results."

    def __init__(self, search_provider: SearchProvider) -> None:
        self._search_provider = search_provider

    async def run(self, query: str, max_results: int = 5) -> list[SearchResult]:
        return await self._search_provider.search(SearchQuery(query=query, max_results=max_results))


class QdrantRetrievalTool:
    name = "qdrant_retrieval"
    description = "Retrieves the most semantically similar chunks from a vector collection."

    def __init__(self, vector_store: VectorStore) -> None:
        self._vector_store = vector_store

    async def run(self, collection: str, query_vector: Vector, limit: int = 10) -> list[VectorMatch]:
        return await self._vector_store.query(collection, query_vector, limit)


class YouTubeLookupTool:
    name = "youtube_lookup"
    description = "Looks up YouTube Data API metadata for a channel or video."

    async def run(self, **kwargs: Any) -> Any:
        raise NotImplementedError("YouTube Data API lookups land in Phase 8")


class ToolRegistry:
    def __init__(self, tools: list[Any]) -> None:
        self._tools: dict[str, Any] = {tool.name: tool for tool in tools}

    def get(self, name: str) -> Any:
        tool = self._tools.get(name)
        if tool is None:
            raise KeyError(f"no tool registered as {name!r}")
        return tool

    def __contains__(self, name: str) -> bool:
        return name in self._tools
