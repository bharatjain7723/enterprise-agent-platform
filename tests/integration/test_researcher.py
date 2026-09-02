import json
from datetime import UTC, datetime

import pytest
from agents import FunctionTool, RunContextWrapper, WebSearchTool
from agents.tool_context import ToolContext

from enterprise_agent_platform.agents.researcher import ResearcherAgent
from enterprise_agent_platform.models.knowledge_document import KnowledgeDocument
from enterprise_agent_platform.models.knowledge_search_result import (
    KnowledgeSearchResult,
)
from enterprise_agent_platform.services.documentation import DocumentationService


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
    run_context: RunContextWrapper[None] = RunContextWrapper(None)

    return ToolContext.from_agent_context(
        run_context,
        tool_call_id="test-call",
        tool_name=tool_name,
        tool_arguments=arguments,
    )


def get_documentation_tool(
    agent: ResearcherAgent,
) -> FunctionTool:
    documentation_tools = [
        tool
        for tool in agent.tools
        if isinstance(tool, FunctionTool) and tool.name == "search_documentation"
    ]

    assert len(documentation_tools) == 1

    return documentation_tools[0]


def test_researcher_agent_has_expected_configuration() -> None:
    searcher = FakeDocumentationSearcher()
    documentation_service = DocumentationService(searcher)

    agent = ResearcherAgent(documentation_service)

    assert agent.name == "Researcher"
    assert agent.output_type.__name__ == "ResearchResult"
    assert len(agent.tools) == 2
    assert len(agent.agent.tools) == 2


def test_researcher_agent_has_web_search_tool() -> None:
    searcher = FakeDocumentationSearcher()
    documentation_service = DocumentationService(searcher)

    agent = ResearcherAgent(documentation_service)

    web_search_tools = [tool for tool in agent.tools if isinstance(tool, WebSearchTool)]

    assert len(web_search_tools) == 1


def test_researcher_agent_has_documentation_search_tool() -> None:
    searcher = FakeDocumentationSearcher()
    documentation_service = DocumentationService(searcher)

    agent = ResearcherAgent(documentation_service)

    documentation_tool = get_documentation_tool(agent)

    assert documentation_tool.name == "search_documentation"


@pytest.mark.asyncio
async def test_researcher_documentation_tool_uses_injected_service() -> None:
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

    searcher = FakeDocumentationSearcher(results=[result])
    documentation_service = DocumentationService(searcher)

    agent = ResearcherAgent(documentation_service)
    documentation_tool = get_documentation_tool(agent)

    arguments = json.dumps({"query": "What is AsyncIO?"})
    context = create_tool_context(
        tool_name=documentation_tool.name,
        arguments=arguments,
    )

    output: str = await documentation_tool.on_invoke_tool(
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
async def test_researcher_documentation_tool_returns_no_results_message() -> None:
    searcher = FakeDocumentationSearcher()
    documentation_service = DocumentationService(searcher)

    agent = ResearcherAgent(documentation_service)
    documentation_tool = get_documentation_tool(agent)

    arguments = json.dumps({"query": "Something unknown"})
    context = create_tool_context(
        tool_name=documentation_tool.name,
        arguments=arguments,
    )

    output: str = await documentation_tool.on_invoke_tool(
        context,
        arguments,
    )

    assert output == "No relevant documentation was found."
    assert searcher.search_call_count == 1
    assert searcher.last_query == "Something unknown"
