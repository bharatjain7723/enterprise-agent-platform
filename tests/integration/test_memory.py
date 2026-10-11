import json

import pytest
from agents import FunctionTool, RunContextWrapper
from agents.tool import invoke_function_tool
from agents.tool_context import ToolContext

from enterprise_agent_platform.memory.in_memory_store import InMemoryMemoryStore
from enterprise_agent_platform.memory.repository import MemoryRepository
from enterprise_agent_platform.memory.service import MemoryService
from enterprise_agent_platform.tools.memory import create_memory_tools


def create_memory_service() -> MemoryService:
    store = InMemoryMemoryStore()
    repository = MemoryRepository(store)

    return MemoryService(repository)


def create_tool_context(
    tool_name: str,
    arguments: str,
) -> ToolContext[None]:
    run_context = RunContextWrapper(None)

    return ToolContext.from_agent_context(
        run_context,
        tool_call_id="integration-test",
        tool_name=tool_name,
        tool_arguments=arguments,
    )


def get_memory_tool(
    tools: tuple[FunctionTool, FunctionTool, FunctionTool],
    name: str,
) -> FunctionTool:
    for tool in tools:
        if tool.name == name:
            return tool

    raise AssertionError(f"Memory tool '{name}' was not found.")


@pytest.mark.asyncio
async def test_memory_end_to_end_remember_recall_forget() -> None:
    # Build the complete memory stack.
    service = create_memory_service()
    tools = create_memory_tools(service)

    remember_tool = get_memory_tool(tools, "remember")
    recall_tool = get_memory_tool(tools, "recall")
    forget_tool = get_memory_tool(tools, "forget")

    # ---------------------------------------------------------
    # 1. Remember
    # ---------------------------------------------------------

    remember_arguments = json.dumps(
        {
            "user_id": "user-1",
            "key": "preferred_language",
            "value": "Python",
        }
    )

    remember_context = create_tool_context(
        "remember",
        remember_arguments,
    )

    remember_result = await invoke_function_tool(
        function_tool=remember_tool,
        context=remember_context,
        arguments=remember_arguments,
    )

    assert remember_result == "Memory saved successfully: preferred_language = Python"

    # ---------------------------------------------------------
    # 2. Verify persistence through the service
    # ---------------------------------------------------------

    memory = await service.recall(
        user_id="user-1",
        key="preferred_language",
    )

    assert memory is not None
    assert memory.user_id == "user-1"
    assert memory.key == "preferred_language"
    assert memory.value == "Python"

    # ---------------------------------------------------------
    # 3. Recall through the actual tool
    # ---------------------------------------------------------

    recall_arguments = json.dumps(
        {
            "user_id": "user-1",
            "key": "preferred_language",
        }
    )

    recall_context = create_tool_context(
        "recall",
        recall_arguments,
    )

    recall_result = await invoke_function_tool(
        function_tool=recall_tool,
        context=recall_context,
        arguments=recall_arguments,
    )

    assert recall_result == "Memory found: preferred_language = Python"

    # ---------------------------------------------------------
    # 4. Forget through the actual tool
    # ---------------------------------------------------------

    forget_arguments = json.dumps(
        {
            "user_id": "user-1",
            "key": "preferred_language",
        }
    )

    forget_context = create_tool_context(
        "forget",
        forget_arguments,
    )

    forget_result = await invoke_function_tool(
        function_tool=forget_tool,
        context=forget_context,
        arguments=forget_arguments,
    )

    assert forget_result == "Memory forgotten successfully: preferred_language"

    # ---------------------------------------------------------
    # 5. Verify the memory is actually gone
    # ---------------------------------------------------------

    memory = await service.recall(
        user_id="user-1",
        key="preferred_language",
    )

    assert memory is None


@pytest.mark.asyncio
async def test_memory_end_to_end_isolates_users() -> None:
    service = create_memory_service()
    tools = create_memory_tools(service)

    remember_tool = get_memory_tool(tools, "remember")
    recall_tool = get_memory_tool(tools, "recall")

    # User 1 remembers Python.
    user_1_arguments = json.dumps(
        {
            "user_id": "user-1",
            "key": "preferred_language",
            "value": "Python",
        }
    )

    user_1_context = create_tool_context(
        "remember",
        user_1_arguments,
    )

    await invoke_function_tool(
        function_tool=remember_tool,
        context=user_1_context,
        arguments=user_1_arguments,
    )

    # User 2 remembers Java using the same key.
    user_2_arguments = json.dumps(
        {
            "user_id": "user-2",
            "key": "preferred_language",
            "value": "Java",
        }
    )

    user_2_context = create_tool_context(
        "remember",
        user_2_arguments,
    )

    await invoke_function_tool(
        function_tool=remember_tool,
        context=user_2_context,
        arguments=user_2_arguments,
    )

    # Recall user 1.
    recall_user_1_arguments = json.dumps(
        {
            "user_id": "user-1",
            "key": "preferred_language",
        }
    )

    recall_user_1_context = create_tool_context(
        "recall",
        recall_user_1_arguments,
    )

    user_1_result = await invoke_function_tool(
        function_tool=recall_tool,
        context=recall_user_1_context,
        arguments=recall_user_1_arguments,
    )

    assert user_1_result == "Memory found: preferred_language = Python"

    # Recall user 2.
    recall_user_2_arguments = json.dumps(
        {
            "user_id": "user-2",
            "key": "preferred_language",
        }
    )

    recall_user_2_context = create_tool_context(
        "recall",
        recall_user_2_arguments,
    )

    user_2_result = await invoke_function_tool(
        function_tool=recall_tool,
        context=recall_user_2_context,
        arguments=recall_user_2_arguments,
    )

    assert user_2_result == "Memory found: preferred_language = Java"
