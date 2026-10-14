from typing import Protocol, TypeVar

from enterprise_agent_platform.models.reflection import ReflectionResult

T_co = TypeVar("T_co", covariant=True)


class RunnableAgent(Protocol[T_co]):
    """Interface for an agent that returns a typed result."""

    async def run(self, user_input: str) -> T_co: ...


class AgentReflectionGenerator:
    """Adapts a text-producing agent to the reflection generator protocol."""

    def __init__(self, agent: RunnableAgent[str]) -> None:
        self.agent = agent

    async def generate(self, task: str) -> str:
        prompt = f"Complete the following task. Produce your best answer.\n\nTask:\n{task}"
        return await self.agent.run(prompt)

    async def revise(
        self,
        task: str,
        draft: str,
        feedback: str,
    ) -> str:
        prompt = (
            "Revise your previous answer using the feedback below.\n"
            "Preserve correct information and address the feedback."
            "\n\n"
            f"Task:\n{task}\n\n"
            f"Previous draft:\n{draft}\n\n"
            f"Feedback:\n{feedback}\n\n"
            "Return the complete revised answer."
        )
        return await self.agent.run(prompt)


class AgentReflector:
    """Adapts a structured-output agent to the reflector protocol."""

    def __init__(
        self,
        agent: RunnableAgent[ReflectionResult],
    ) -> None:
        self.agent = agent

    async def review(
        self,
        task: str,
        draft: str,
    ) -> ReflectionResult:
        prompt = (
            "Review the draft against the task requirements.\n"
            "Approve it only if it satisfies the requirements. "
            "Otherwise, explain the specific changes needed.\n\n"
            f"Task:\n{task}\n\n"
            f"Draft:\n{draft}"
        )
        return await self.agent.run(prompt)
