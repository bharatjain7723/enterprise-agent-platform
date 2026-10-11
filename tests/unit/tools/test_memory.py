import json

import pytest
from agents import FunctionTool, RunContextWrapper
from agents.tool import invoke_function_tool
from agents.tool_context import ToolContext

from enterprise_agent_platform.memory.in_memory_store import InMemoryMemoryStore
from enterprise_agent_platform.memory.repository import MemoryRepository
from enterprise_agent_platform.memory.service import MemoryService
from enterprise_agent_platform.tools.memory import create_memory_tools


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


@pytest.fixture
def service() -> MemoryService:
    store = InMemoryMemoryStore()
    repository = MemoryRepository(store)

    return MemoryService(repository)


@pytest.fixture
def memory_tools(
    service: MemoryService,
) -> tuple[FunctionTool, FunctionTool, FunctionTool]:
    return create_memory_tools(service)


@pytest.fixture
def remember_tool(
    memory_tools: tuple[FunctionTool, FunctionTool, FunctionTool],
) -> FunctionTool:
    return memory_tools[0]


@pytest.fixture
def recall_tool(
    memory_tools: tuple[FunctionTool, FunctionTool, FunctionTool],
) -> FunctionTool:
    return memory_tools[1]


@pytest.fixture
def forget_tool(
    memory_tools: tuple[FunctionTool, FunctionTool, FunctionTool],
) -> FunctionTool:
    return memory_tools[2]


@pytest.mark.asyncio
async def test_create_memory_tools_returns_three_tools(
    memory_tools: tuple[FunctionTool, FunctionTool, FunctionTool],
) -> None:
    assert len(memory_tools) == 3

    names = [tool.name for tool in memory_tools]

    assert names == ["remember", "recall", "forget"]


@pytest.mark.asyncio
async def test_remember_tool_saves_memory(
    remember_tool: FunctionTool,
) -> None:
    arguments = json.dumps(
        {
            "user_id": "user-1",
            "key": "preferred_language",
            "value": "Python",
        }
    )

    context = create_tool_context(
        "remember",
        arguments,
    )

    result = await invoke_function_tool(
        function_tool=remember_tool,
        context=context,
        arguments=arguments,
    )

    assert result == "Memory saved successfully: preferred_language = Python"


@pytest.mark.asyncio
async def test_remember_tool_persists_memory(
    service: MemoryService,
    remember_tool: FunctionTool,
) -> None:
    arguments = json.dumps(
        {
            "user_id": "user-1",
            "key": "preferred_language",
            "value": "Python",
        }
    )

    context = create_tool_context(
        "remember",
        arguments,
    )

    await invoke_function_tool(
        function_tool=remember_tool,
        context=context,
        arguments=arguments,
    )

    memory = await service.recall(
        user_id="user-1",
        key="preferred_language",
    )

    assert memory is not None
    assert memory.value == "Python"


@pytest.mark.asyncio
async def test_recall_tool_returns_existing_memory(
    service: MemoryService,
    recall_tool: FunctionTool,
) -> None:
    await service.remember(
        user_id="user-1",
        key="preferred_language",
        value="Python",
    )

    arguments = json.dumps(
        {
            "user_id": "user-1",
            "key": "preferred_language",
        }
    )

    context = create_tool_context(
        "recall",
        arguments,
    )

    result = await invoke_function_tool(
        function_tool=recall_tool,
        context=context,
        arguments=arguments,
    )

    assert result == "Memory found: preferred_language = Python"


@pytest.mark.asyncio
async def test_recall_tool_returns_no_memory_message(
    recall_tool: FunctionTool,
) -> None:
    arguments = json.dumps(
        {
            "user_id": "user-1",
            "key": "preferred_language",
        }
    )

    context = create_tool_context(
        "recall",
        arguments,
    )

    result = await invoke_function_tool(
        function_tool=recall_tool,
        context=context,
        arguments=arguments,
    )

    assert result == "No memory was found."


@pytest.mark.asyncio
async def test_forget_tool_removes_memory(
    service: MemoryService,
    forget_tool: FunctionTool,
) -> None:
    await service.remember(
        user_id="user-1",
        key="preferred_language",
        value="Python",
    )

    arguments = json.dumps(
        {
            "user_id": "user-1",
            "key": "preferred_language",
        }
    )

    context = create_tool_context(
        "forget",
        arguments,
    )

    result = await invoke_function_tool(
        function_tool=forget_tool,
        context=context,
        arguments=arguments,
    )

    assert result == "Memory forgotten successfully: preferred_language"

    memory = await service.recall(
        user_id="user-1",
        key="preferred_language",
    )

    assert memory is None


@pytest.mark.asyncio
async def test_forget_missing_memory_is_successful(
    forget_tool: FunctionTool,
) -> None:
    arguments = json.dumps(
        {
            "user_id": "user-1",
            "key": "preferred_language",
        }
    )

    context = create_tool_context(
        "forget",
        arguments,
    )

    result = await invoke_function_tool(
        function_tool=forget_tool,
        context=context,
        arguments=arguments,
    )

    assert result == "Memory forgotten successfully: preferred_language"


@pytest.mark.asyncio
async def test_memory_tools_are_isolated_by_user(
    service: MemoryService,
    recall_tool: FunctionTool,
) -> None:
    await service.remember(
        user_id="user-1",
        key="preferred_language",
        value="Python",
    )

    await service.remember(
        user_id="user-2",
        key="preferred_language",
        value="Java",
    )

    arguments = json.dumps(
        {
            "user_id": "user-1",
            "key": "preferred_language",
        }
    )

    context = create_tool_context(
        "recall",
        arguments,
    )

    result = await invoke_function_tool(
        function_tool=recall_tool,
        context=context,
        arguments=arguments,
    )

    assert result == "Memory found: preferred_language = Python"
