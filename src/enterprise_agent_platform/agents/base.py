from dataclasses import dataclass, field
from typing import TypeVar

from agents import Agent, RunConfig, Runner, Tool

T = TypeVar("T")


@dataclass
class BaseAgent[T]:
    """Base class implemented by every platform agent."""

    name: str
    description: str
    instructions: str
    output_type: type[T]
    tools: list[Tool] = field(default_factory=list)

    agent: Agent[T] = field(init=False)

    def __post_init__(self) -> None:
        self.agent = Agent(
            name=self.name,
            instructions=self.instructions,
            tools=self.tools,
            output_type=self.output_type,
        )

    async def run(self, user_input: str) -> T:
        """Run the agent with the provided input."""

        result = await Runner.run(
            self.agent,
            input=user_input,
            run_config=RunConfig(
                workflow_name=f"{self.name} Workflow",
                trace_metadata={
                    "agent_name": self.name,
                    "agent_description": self.description,
                },
            ),
        )

        return result.final_output
