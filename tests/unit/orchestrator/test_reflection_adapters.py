import pytest

from enterprise_agent_platform.models.reflection import ReflectionResult
from enterprise_agent_platform.orchestration.reflection_adapters import (
    AgentReflectionGenerator,
    AgentReflector,
)


class FakeTextAgent:
    def __init__(self, outputs: list[str]) -> None:
        self.outputs = list(outputs)
        self.inputs: list[str] = []

    async def run(self, user_input: str) -> str:
        self.inputs.append(user_input)

        if not self.outputs:
            raise AssertionError("No output configured.")

        return self.outputs.pop(0)


class FakeReflectionAgent:
    def __init__(self, result: ReflectionResult) -> None:
        self.result = result
        self.inputs: list[str] = []

    async def run(self, user_input: str) -> ReflectionResult:
        self.inputs.append(user_input)
        return self.result


@pytest.mark.asyncio
async def test_generator_creates_initial_draft() -> None:
    agent = FakeTextAgent(["Initial answer"])
    generator = AgentReflectionGenerator(agent)

    result = await generator.generate("Implement a parser")

    assert result == "Initial answer"
    assert len(agent.inputs) == 1
    assert "Implement a parser" in agent.inputs[0]
    assert "best answer" in agent.inputs[0]


@pytest.mark.asyncio
async def test_generator_revises_draft_using_feedback() -> None:
    agent = FakeTextAgent(["Improved answer"])
    generator = AgentReflectionGenerator(agent)

    result = await generator.revise(
        task="Implement a parser",
        draft="Original answer",
        feedback="Handle empty input.",
    )

    assert result == "Improved answer"
    assert len(agent.inputs) == 1
    assert "Implement a parser" in agent.inputs[0]
    assert "Original answer" in agent.inputs[0]
    assert "Handle empty input." in agent.inputs[0]
    assert "complete revised answer" in agent.inputs[0]


@pytest.mark.asyncio
async def test_reflector_returns_structured_result() -> None:
    expected = ReflectionResult(
        approved=False,
        feedback="Handle empty input.",
    )
    agent = FakeReflectionAgent(expected)
    reflector = AgentReflector(agent)

    result = await reflector.review(
        task="Implement a parser",
        draft="Original answer",
    )

    assert result == expected
    assert result.approved is False
    assert result.feedback == "Handle empty input."
    assert len(agent.inputs) == 1
    assert "Implement a parser" in agent.inputs[0]
    assert "Original answer" in agent.inputs[0]


@pytest.mark.asyncio
async def test_reflector_includes_task_and_draft_in_review_prompt() -> None:
    agent = FakeReflectionAgent(
        ReflectionResult(
            approved=True,
            feedback="Meets requirements.",
        )
    )
    reflector = AgentReflector(agent)

    await reflector.review(
        task="Validate user input",
        draft="The implementation validates input.",
    )

    prompt = agent.inputs[0]

    assert "Validate user input" in prompt
    assert "The implementation validates input." in prompt
    assert "Approve it only if" in prompt


@pytest.mark.asyncio
async def test_generator_propagates_agent_errors() -> None:
    class FailingAgent:
        async def run(self, user_input: str) -> str:
            raise RuntimeError("Agent execution failed")

    generator = AgentReflectionGenerator(FailingAgent())

    with pytest.raises(RuntimeError, match="Agent execution failed"):
        await generator.generate("Implement a parser")


@pytest.mark.asyncio
async def test_reflector_propagates_agent_errors() -> None:
    class FailingAgent:
        async def run(self, user_input: str) -> ReflectionResult:
            raise RuntimeError("Critic execution failed")

    reflector = AgentReflector(FailingAgent())

    with pytest.raises(RuntimeError, match="Critic execution failed"):
        await reflector.review("Implement a parser", "Draft")
