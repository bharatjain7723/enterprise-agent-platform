from types import SimpleNamespace
from typing import Any

import pytest

from enterprise_agent_platform.agents.base import BaseAgent
from enterprise_agent_platform.guardrails import (
    GuardrailViolationError,
    MaxInputLengthGuardrail,
    NonEmptyInputGuardrail,
    NonEmptyOutputGuardrail,
)


def make_test_agent() -> BaseAgent[str]:
    return BaseAgent(
        name="Test Agent",
        description="Agent used for guardrail integration tests",
        instructions="Return a short answer.",
        output_type=str,
    )


@pytest.mark.asyncio
async def test_rejected_input_prevents_agent_execution(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    agent = make_test_agent()
    agent.input_guardrails = [NonEmptyInputGuardrail()]

    async def unexpected_runner_call(*args: Any, **kwargs: Any) -> Any:
        pytest.fail("Runner.run must not be called for rejected input")

    monkeypatch.setattr(
        "enterprise_agent_platform.agents.base.Runner.run",
        unexpected_runner_call,
    )

    with pytest.raises(GuardrailViolationError, match="Input rejected"):
        await agent.run("   ")


@pytest.mark.asyncio
async def test_accepted_input_executes_agent(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    agent = make_test_agent()
    agent.input_guardrails = [NonEmptyInputGuardrail()]
    agent.output_guardrails = [NonEmptyOutputGuardrail()]

    async def fake_runner_call(*args: Any, **kwargs: Any) -> Any:
        return SimpleNamespace(final_output="Answer")

    monkeypatch.setattr(
        "enterprise_agent_platform.agents.base.Runner.run",
        fake_runner_call,
    )

    output = await agent.run("Explain Python.")

    assert output == "Answer"


@pytest.mark.asyncio
async def test_rejected_output_is_not_returned(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    agent = make_test_agent()
    agent.output_guardrails = [NonEmptyOutputGuardrail()]

    async def fake_runner_call(*args: Any, **kwargs: Any) -> Any:
        return SimpleNamespace(final_output="   ")

    monkeypatch.setattr(
        "enterprise_agent_platform.agents.base.Runner.run",
        fake_runner_call,
    )

    with pytest.raises(GuardrailViolationError, match="Output rejected"):
        await agent.run("Explain Python.")


def test_agent_has_default_guardrails() -> None:
    agent = make_test_agent()

    assert len(agent.input_guardrails) == 2
    assert isinstance(agent.input_guardrails[0], NonEmptyInputGuardrail)
    assert isinstance(agent.input_guardrails[1], MaxInputLengthGuardrail)
    assert len(agent.output_guardrails) == 1
    assert isinstance(agent.output_guardrails[0], NonEmptyOutputGuardrail)
