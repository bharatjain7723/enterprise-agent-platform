from typing import Any, Protocol


class AgentRunner(Protocol):
    """Interface for an agent that can execute a task."""

    async def run(self, user_input: str) -> Any:
        """Execute the agent with the provided input."""
        ...
