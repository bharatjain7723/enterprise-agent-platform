from typing import Protocol

from enterprise_agent_platform.models.guardrail import GuardrailResult


class InputGuardrail(Protocol):
    """Interface for checks applied before agent execution."""

    def check(self, user_input: str) -> GuardrailResult: ...


class OutputGuardrail(Protocol):
    """Interface for checks applied to an agent's final output."""

    def check(self, output: object) -> GuardrailResult: ...


class GuardrailViolationError(Exception):
    """Raised when a guardrail rejects input or output."""
