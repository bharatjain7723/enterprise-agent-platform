import json
from datetime import UTC, datetime

import pytest
from agents import RunContextWrapper
from agents.tool_context import ToolContext

from enterprise_agent_platform.models.knowledge_document import (
    KnowledgeDocument,
)
from enterprise_agent_platform.models.knowledge_search_result import (
    KnowledgeSearchResult,
)
from enterprise_agent_platform.tools.documentation_search import (
    create_documentation_search_tool,
)


class FakeDocumentationSearcher:
    def __init__(
        self,
        results: list[KnowledgeSearchResult] | None = None,
    ) -> None:
        self.results = results if results is not None else []
        self.search_call_count = 0
        self.last_query: str | None = None

    async def search(
        self,
        query: str,
    ) -> list[KnowledgeSearchResult]:
        self.search_call_count += 1
        self.last_query = query
        return self.results


def create_tool_context(
    tool_name: str,
    arguments: str,
) -> ToolContext[None]:
    run_context = RunContextWrapper(None)

    return ToolContext.from_agent_context(
        run_context,
        tool_call_id="test-call",
        tool_name=tool_name,
        tool_arguments=arguments,
    )


@pytest.mark.asyncio
async def test_search_documentation_returns_formatted_results() -> None:
    document = KnowledgeDocument(
        id="doc-1",
        title="AsyncIO",
        content="AsyncIO provides asynchronous programming support.",
        source="python/asyncio.md",
        updated_at=datetime.now(UTC),
    )

    result = KnowledgeSearchResult(
        document=document,
        score=0.91234,
        snippet="",
    )

    searcher = FakeDocumentationSearcher(
        results=[result],
    )

    tool = create_documentation_search_tool(searcher)

    arguments = json.dumps(
        {"query": "What is AsyncIO?"},
    )

    context = create_tool_context(
        tool_name=tool.name,
        arguments=arguments,
    )

    output: str = await tool.on_invoke_tool(
        context,
        arguments,
    )

    assert "[1] AsyncIO" in output
    assert "Source: python/asyncio.md" in output
    assert "Relevance: 0.912" in output
    assert "AsyncIO provides asynchronous programming support." in output

    assert searcher.search_call_count == 1
    assert searcher.last_query == "What is AsyncIO?"


@pytest.mark.asyncio
async def test_search_documentation_returns_message_when_no_results() -> None:
    searcher = FakeDocumentationSearcher()

    tool = create_documentation_search_tool(searcher)

    arguments = json.dumps(
        {"query": "Something unknown"},
    )

    context = create_tool_context(
        tool_name=tool.name,
        arguments=arguments,
    )

    output: str = await tool.on_invoke_tool(
        context,
        arguments,
    )

    assert output == "No relevant documentation was found."

    assert searcher.search_call_count == 1
    assert searcher.last_query == "Something unknown"


@pytest.mark.asyncio
async def test_search_documentation_formats_multiple_results() -> None:
    updated_at = datetime.now(UTC)

    first = KnowledgeSearchResult(
        document=KnowledgeDocument(
            id="doc-1",
            title="AsyncIO",
            content="AsyncIO documentation.",
            source="python/asyncio.md",
            updated_at=updated_at,
        ),
        score=0.95,
        snippet="",
    )

    second = KnowledgeSearchResult(
        document=KnowledgeDocument(
            id="doc-2",
            title="Agents SDK",
            content="Agents SDK documentation.",
            source="agents/sdk.md",
            updated_at=updated_at,
        ),
        score=0.82,
        snippet="",
    )

    searcher = FakeDocumentationSearcher(
        results=[first, second],
    )

    tool = create_documentation_search_tool(searcher)

    arguments = json.dumps(
        {"query": "agents and async programming"},
    )

    context = create_tool_context(
        tool_name=tool.name,
        arguments=arguments,
    )

    output: str = await tool.on_invoke_tool(
        context,
        arguments,
    )

    assert "[1] AsyncIO" in output
    assert "Relevance: 0.950" in output

    assert "[2] Agents SDK" in output
    assert "Relevance: 0.820" in output

    assert output.index("[1] AsyncIO") < output.index("[2] Agents SDK")

    assert searcher.search_call_count == 1
    assert searcher.last_query == "agents and async programming"
