from agents import FunctionTool

from enterprise_agent_platform.agents.researcher import ResearcherAgent
from enterprise_agent_platform.memory.in_memory_store import InMemoryMemoryStore
from enterprise_agent_platform.memory.repository import MemoryRepository
from enterprise_agent_platform.memory.service import MemoryService
from enterprise_agent_platform.models.knowledge_search_result import (
    KnowledgeSearchResult,
)
from enterprise_agent_platform.services.documentation import DocumentationService


class FakeDocumentationSearcher:
    async def search(
        self,
        query: str,
    ) -> list[KnowledgeSearchResult]:
        return []


def create_documentation_service() -> DocumentationService:
    searcher = FakeDocumentationSearcher()

    return DocumentationService(searcher)


def create_memory_service() -> MemoryService:
    store = InMemoryMemoryStore()
    repository = MemoryRepository(store)

    return MemoryService(repository)


def get_tool_names(agent: ResearcherAgent) -> list[str]:
    return [tool.name for tool in agent.agent.tools]


def get_function_tool(
    agent: ResearcherAgent,
    tool_name: str,
) -> FunctionTool:
    for tool in agent.agent.tools:
        if tool.name == tool_name:
            if isinstance(tool, FunctionTool):
                return tool

            raise AssertionError(f"Tool '{tool_name}' is not a FunctionTool.")

    raise AssertionError(f"Tool '{tool_name}' was not found on the ResearcherAgent.")


def test_researcher_without_memory_has_existing_tools() -> None:
    documentation_service = create_documentation_service()

    researcher = ResearcherAgent(
        documentation_service=documentation_service,
    )

    tool_names = get_tool_names(researcher)

    assert "search_documentation" in tool_names
    assert len(tool_names) == 2


def test_researcher_with_memory_has_memory_tools() -> None:
    documentation_service = create_documentation_service()
    memory_service = create_memory_service()

    researcher = ResearcherAgent(
        documentation_service=documentation_service,
        memory_service=memory_service,
    )

    tool_names = get_tool_names(researcher)

    assert "search_documentation" in tool_names
    assert "remember" in tool_names
    assert "recall" in tool_names
    assert "forget" in tool_names
    assert len(tool_names) == 5


def test_researcher_memory_tools_are_function_tools() -> None:
    documentation_service = create_documentation_service()
    memory_service = create_memory_service()

    researcher = ResearcherAgent(
        documentation_service=documentation_service,
        memory_service=memory_service,
    )

    remember_tool = get_function_tool(
        researcher,
        "remember",
    )

    recall_tool = get_function_tool(
        researcher,
        "recall",
    )

    forget_tool = get_function_tool(
        researcher,
        "forget",
    )

    assert isinstance(remember_tool, FunctionTool)
    assert isinstance(recall_tool, FunctionTool)
    assert isinstance(forget_tool, FunctionTool)


def test_researcher_without_memory_does_not_expose_memory_tools() -> None:
    documentation_service = create_documentation_service()

    researcher = ResearcherAgent(
        documentation_service=documentation_service,
    )

    tool_names = get_tool_names(researcher)

    assert "remember" not in tool_names
    assert "recall" not in tool_names
    assert "forget" not in tool_names


def test_researcher_memory_tools_are_registered_from_supplied_service() -> None:
    documentation_service = create_documentation_service()
    memory_service = create_memory_service()

    researcher = ResearcherAgent(
        documentation_service=documentation_service,
        memory_service=memory_service,
    )

    remember_tool = get_function_tool(
        researcher,
        "remember",
    )

    recall_tool = get_function_tool(
        researcher,
        "recall",
    )

    forget_tool = get_function_tool(
        researcher,
        "forget",
    )

    assert remember_tool.name == "remember"
    assert recall_tool.name == "recall"
    assert forget_tool.name == "forget"
