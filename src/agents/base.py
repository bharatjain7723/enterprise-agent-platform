from dataclasses import dataclass, field

from agents import Agent, Runner


@dataclass
class BaseAgent:
    """Base class implemented by every platform agent."""

    name: str
    description: str
    instructions: str

    agent: Agent = field(init=False)

    def __post_init__(self) -> None:
        self.agent = Agent(
            name=self.name,
            instructions=self.instructions,
        )

    async def run(self, user_input: str) -> str:
        """Run the agent with the provided input."""

        result = await Runner.run(
            self.agent,
            input=user_input,
        )

        return result.final_output
