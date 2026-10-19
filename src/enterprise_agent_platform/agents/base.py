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
from enterprise_agent_platform.guardrails import (
    GuardrailViolationError,
    InputGuardrail,
    MaxInputLengthGuardrail,
    NonEmptyInputGuardrail,
    NonEmptyOutputGuardrail,
    OutputGuardrail,
)

T = TypeVar("T")


def default_input_guardrails() -> list[InputGuardrail]:
    """Create the default input guardrails for an agent."""

    return [
        NonEmptyInputGuardrail(),
        MaxInputLengthGuardrail(),
    ]


def default_output_guardrails() -> list[OutputGuardrail]:
    """Create the default output guardrails for an agent."""

    return [NonEmptyOutputGuardrail()]


@dataclass
class BaseAgent[T]:
    """Base class implemented by every platform agent."""

    name: str
    description: str
    instructions: str
    output_type: type[T]
    tools: list[Tool] = field(default_factory=lambda: list[Tool]())
    model: str | None = None
    input_guardrails: list[InputGuardrail] = field(default_factory=default_input_guardrails)
    output_guardrails: list[OutputGuardrail] = field(default_factory=default_output_guardrails)

    agent: Agent[T] = field(init=False)

    def __post_init__(self) -> None:
        self.agent = Agent(
            name=self.name,
            instructions=self.instructions,
            tools=self.tools,
            output_type=self.output_type,
            model=self.model,
        )

    async def run(self, user_input: str) -> T:
        """Validate input, execute the agent, and validate its output."""

        self._check_input(user_input)

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

        final_output = result.final_output
        self._check_output(final_output)

        return final_output

    def _check_input(self, user_input: str) -> None:
        """Run input guardrails in order and reject on the first failure."""

        for guardrail in self.input_guardrails:
            result = guardrail.check(user_input)

            if not result.allowed:
                raise GuardrailViolationError(
                    f"Input rejected by '{result.guardrail_name}': {result.reason}"
                )

    def _check_output(self, output: object) -> None:
        """Run output guardrails in order and reject on the first failure."""

        for guardrail in self.output_guardrails:
            result = guardrail.check(output)

            if not result.allowed:
                raise GuardrailViolationError(
                    f"Output rejected by '{result.guardrail_name}': {result.reason}"
                )
