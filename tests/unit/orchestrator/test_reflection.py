import pytest

from enterprise_agent_platform.models.reflection import ReflectionResult
from enterprise_agent_platform.orchestration.reflection import (
    ReflectionOrchestrator,
)


class FakeGenerator:
    def __init__(
        self,
        initial_draft: str = "initial draft",
        revised_drafts: list[str] | None = None,
    ) -> None:
        self.initial_draft = initial_draft
        self.revised_drafts = list(revised_drafts or [])
        self.generate_calls: list[str] = []
        self.revise_calls: list[tuple[str, str, str]] = []

    async def generate(self, task: str) -> str:
        self.generate_calls.append(task)
        return self.initial_draft

    async def revise(
        self,
        task: str,
        draft: str,
        feedback: str,
    ) -> str:
        self.revise_calls.append((task, draft, feedback))

        if not self.revised_drafts:
            raise AssertionError("No revised draft configured.")

        return self.revised_drafts.pop(0)


class FakeReflector:
    def __init__(
        self,
        results: list[ReflectionResult],
    ) -> None:
        self.results = list(results)
        self.review_calls: list[tuple[str, str]] = []

    async def review(
        self,
        task: str,
        draft: str,
    ) -> ReflectionResult:
        self.review_calls.append((task, draft))

        if not self.results:
            raise AssertionError("No reflection result configured.")

        return self.results.pop(0)


def approved(feedback: str = "Meets the requirements.") -> ReflectionResult:
    return ReflectionResult(approved=True, feedback=feedback)


def rejected(feedback: str = "Handle empty input.") -> ReflectionResult:
    return ReflectionResult(approved=False, feedback=feedback)


@pytest.mark.asyncio
async def test_approved_initial_draft_returns_one_attempt() -> None:
    generator = FakeGenerator(initial_draft="correct draft")
    reflector = FakeReflector([approved()])
    orchestrator = ReflectionOrchestrator(generator, reflector)

    history = await orchestrator.run("Implement parser")

    assert len(history) == 1
    assert history[0].output == "correct draft"
    assert history[0].reflection.approved is True
    assert generator.revise_calls == []


@pytest.mark.asyncio
async def test_rejected_draft_is_revised_and_approved() -> None:
    generator = FakeGenerator(
        initial_draft="first draft",
        revised_drafts=["improved draft"],
    )
    reflector = FakeReflector([rejected(), approved()])
    orchestrator = ReflectionOrchestrator(generator, reflector)

    history = await orchestrator.run("Implement parser")

    assert len(history) == 2
    assert history[0].output == "first draft"
    assert history[0].reflection.approved is False
    assert history[1].output == "improved draft"
    assert history[1].reflection.approved is True
    assert generator.revise_calls == [("Implement parser", "first draft", "Handle empty input.")]


@pytest.mark.asyncio
async def test_max_attempts_prevents_an_infinite_loop() -> None:
    generator = FakeGenerator(
        initial_draft="first draft",
        revised_drafts=["second draft"],
    )
    reflector = FakeReflector([rejected(), rejected()])
    orchestrator = ReflectionOrchestrator(
        generator,
        reflector,
        max_attempts=2,
    )

    history = await orchestrator.run("Implement parser")

    assert len(history) == 2
    assert history[-1].output == "second draft"
    assert history[-1].reflection.approved is False
    assert len(generator.revise_calls) == 1


@pytest.mark.asyncio
async def test_revision_receives_previous_feedback() -> None:
    generator = FakeGenerator(revised_drafts=["revised"])
    reflector = FakeReflector([rejected("Add validation."), approved()])
    orchestrator = ReflectionOrchestrator(generator, reflector)

    await orchestrator.run("Implement parser")

    assert generator.revise_calls[0][2] == "Add validation."


@pytest.mark.asyncio
async def test_stops_immediately_when_first_draft_is_approved() -> None:
    generator = FakeGenerator()
    reflector = FakeReflector([approved()])
    orchestrator = ReflectionOrchestrator(generator, reflector)

    history = await orchestrator.run("Task")

    assert len(history) == 1
    assert len(reflector.review_calls) == 1
    assert generator.revise_calls == []


@pytest.mark.asyncio
async def test_rejects_max_attempts_less_than_one() -> None:
    generator = FakeGenerator()
    reflector = FakeReflector([approved()])

    with pytest.raises(ValueError, match="max_attempts must be at least 1"):
        ReflectionOrchestrator(generator, reflector, max_attempts=0)


@pytest.mark.asyncio
async def test_rejects_empty_task() -> None:
    generator = FakeGenerator()
    reflector = FakeReflector([approved()])
    orchestrator = ReflectionOrchestrator(generator, reflector)

    with pytest.raises(ValueError, match="Task cannot be empty"):
        await orchestrator.run("   ")

    assert generator.generate_calls == []


@pytest.mark.asyncio
async def test_single_attempt_does_not_revise_rejected_draft() -> None:
    generator = FakeGenerator(initial_draft="draft")
    reflector = FakeReflector([rejected()])
    orchestrator = ReflectionOrchestrator(
        generator,
        reflector,
        max_attempts=1,
    )

    history = await orchestrator.run("Task")

    assert len(history) == 1
    assert history[0].reflection.approved is False
    assert generator.revise_calls == []


@pytest.mark.asyncio
async def test_reflector_receives_each_draft_in_order() -> None:
    generator = FakeGenerator(
        initial_draft="draft 1",
        revised_drafts=["draft 2"],
    )
    reflector = FakeReflector([rejected(), approved()])
    orchestrator = ReflectionOrchestrator(generator, reflector)

    await orchestrator.run("Task")

    assert reflector.review_calls == [
        ("Task", "draft 1"),
        ("Task", "draft 2"),
    ]


@pytest.mark.asyncio
async def test_generator_error_propagates() -> None:
    class FailingGenerator(FakeGenerator):
        async def generate(self, task: str) -> str:
            raise RuntimeError("generation failed")

    orchestrator = ReflectionOrchestrator(
        FailingGenerator(),
        FakeReflector([approved()]),
    )

    with pytest.raises(RuntimeError, match="generation failed"):
        await orchestrator.run("Task")


@pytest.mark.asyncio
async def test_reflector_error_propagates() -> None:
    class FailingReflector(FakeReflector):
        async def review(
            self,
            task: str,
            draft: str,
        ) -> ReflectionResult:
            raise RuntimeError("review failed")

    orchestrator = ReflectionOrchestrator(
        FakeGenerator(),
        FailingReflector([]),
    )

    with pytest.raises(RuntimeError, match="review failed"):
        await orchestrator.run("Task")
