from dataclasses import dataclass, field
from typing import TypeVar

from agents import Agent, RunConfig, Runner, Tool
from agents.exceptions import (
    MaxTurnsExceeded,
    ModelBehaviorError,
    ToolTimeoutError,
    UserError,
)

from enterprise_agent_platform.exceptions import (
    NonRetryableError,
    RetryableError,
)

T = TypeVar("T")


@dataclass
class BaseAgent[T]:
    """Base class implemented by every platform agent."""

    name: str
    description: str
    instructions: str
    output_type: type[T]
    tools: list[Tool] = field(default_factory=lambda: list[Tool]())

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

        try:
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

        except ToolTimeoutError as exc:
            raise RetryableError(f"Agent '{self.name}' encountered a tool timeout: {exc}") from exc

        except MaxTurnsExceeded as exc:
            raise NonRetryableError(
                f"Agent '{self.name}' exceeded its maximum turns: {exc}"
            ) from exc

        except ModelBehaviorError as exc:
            raise NonRetryableError(
                f"Agent '{self.name}' produced invalid model behavior: {exc}"
            ) from exc

        except UserError as exc:
            raise NonRetryableError(
                f"Agent '{self.name}' encountered an SDK configuration error: {exc}"
            ) from exc
