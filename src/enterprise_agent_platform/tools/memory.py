from agents import FunctionTool, function_tool

from enterprise_agent_platform.memory.service import MemoryService


def create_memory_tools(
    service: MemoryService,
) -> tuple[FunctionTool, FunctionTool, FunctionTool]:
    @function_tool
    async def remember(
        user_id: str,
        key: str,
        value: str,
    ) -> str:
        """Store a useful piece of information about a user.

        Use this when the user explicitly asks you to remember
        a preference, decision, or other useful information.
        """
        memory = await service.remember(
            user_id=user_id,
            key=key,
            value=value,
        )

        return f"Memory saved successfully: {memory.key} = {memory.value}"

    @function_tool
    async def recall(
        user_id: str,
        key: str,
    ) -> str:
        """Retrieve a previously stored memory for a user."""
        memory = await service.recall(
            user_id=user_id,
            key=key,
        )

        if memory is None:
            return "No memory was found."

        return f"Memory found: {memory.key} = {memory.value}"

    @function_tool
    async def forget(
        user_id: str,
        key: str,
    ) -> str:
        """Forget a previously stored memory for a user."""
        await service.forget(
            user_id=user_id,
            key=key,
        )

        return f"Memory forgotten successfully: {key}"

    return remember, recall, forget
