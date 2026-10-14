from typing import Protocol

from enterprise_agent_platform.models.reflection import (
    ReflectionAttempt,
    ReflectionResult,
)


class ReflectionGenerator(Protocol):
    async def generate(self, task: str) -> str: ...

    async def revise(self, task: str, draft: str, feedback: str) -> str: ...


class Reflector(Protocol):
    async def review(
        self,
        task: str,
        draft: str,
    ) -> ReflectionResult: ...


class ReflectionOrchestrator:
    def __init__(
        self,
        generator: ReflectionGenerator,
        reflector: Reflector,
        max_attempts: int = 3,
    ) -> None:
        if max_attempts < 1:
            raise ValueError("max_attempts must be at least 1.")

        self.generator = generator
        self.reflector = reflector
        self.max_attempts = max_attempts

    async def run(self, task: str) -> list[ReflectionAttempt]:
        if not task.strip():
            raise ValueError("Task cannot be empty.")

        draft = await self.generator.generate(task)
        history: list[ReflectionAttempt] = []

        for attempt_number in range(1, self.max_attempts + 1):
            reflection = await self.reflector.review(task, draft)

            history.append(
                ReflectionAttempt(
                    attempt=attempt_number,
                    output=draft,
                    reflection=reflection,
                )
            )

            if reflection.approved:
                break

            if attempt_number < self.max_attempts:
                draft = await self.generator.revise(
                    task=task,
                    draft=draft,
                    feedback=reflection.feedback,
                )

        return history
