import asyncio
import time

import pytest
from pydantic import BaseModel

from enterprise_agent_platform.models.plan import Plan
from enterprise_agent_platform.models.task import Task
from enterprise_agent_platform.models.worker_type import WorkerType
from enterprise_agent_platform.orchestration.registry import AgentRegistry
from enterprise_agent_platform.orchestration.validator import PlanValidator
from enterprise_agent_platform.orchestration.worker import WorkerOrchestrator


class FakeResult(BaseModel):
    message: str


class FakeAgent:
    """Fake agent used to test orchestration without calling an LLM."""

    def __init__(
        self,
        name: str,
        delay: float = 0.1,
    ) -> None:
        self.name = name
        self.delay = delay

    async def run(
        self,
        user_input: str,
    ) -> FakeResult:
        await asyncio.sleep(self.delay)

        return FakeResult(message=f"{self.name} completed task.")


def create_task(
    task_id: str,
    agent: WorkerType,
    depends_on: list[str] | None = None,
) -> Task:
    return Task(
        id=task_id,
        description=f"Execute {task_id}",
        agent=agent,
        depends_on=depends_on or [],
    )


def create_orchestrator(
    delay: float = 0.1,
) -> WorkerOrchestrator:
    registry = AgentRegistry()

    registry.register(
        WorkerType.RESEARCHER,
        FakeAgent(
            name="Fake Researcher",
            delay=delay,
        ),
    )

    registry.register(
        WorkerType.CODER,
        FakeAgent(
            name="Fake Coder",
            delay=delay,
        ),
    )

    return WorkerOrchestrator(
        registry=registry,
        validator=PlanValidator(),
    )


@pytest.mark.asyncio
async def test_executes_dependency_chain() -> None:
    """
    task_1
       |
       v
    task_2
    """

    plan = Plan(
        objective="Test dependency chain",
        assumptions=[],
        tasks=[
            create_task(
                "task_1",
                WorkerType.RESEARCHER,
            ),
            create_task(
                "task_2",
                WorkerType.CODER,
                ["task_1"],
            ),
        ],
    )

    worker = create_orchestrator()

    results = await worker.execute(plan)

    assert len(results) == 2
    assert "task_1" in results
    assert "task_2" in results

    assert results["task_1"].output.message == "Fake Researcher completed task."

    assert results["task_2"].output.message == "Fake Coder completed task."


@pytest.mark.asyncio
async def test_executes_branching_dag() -> None:
    """
                task_1
                /    \
               v      v
            task_2  task_3
               \\      /
                v    v
                task_4
    """

    plan = Plan(
        objective="Test branching DAG",
        assumptions=[],
        tasks=[
            create_task(
                "task_1",
                WorkerType.RESEARCHER,
            ),
            create_task(
                "task_2",
                WorkerType.RESEARCHER,
                ["task_1"],
            ),
            create_task(
                "task_3",
                WorkerType.RESEARCHER,
                ["task_1"],
            ),
            create_task(
                "task_4",
                WorkerType.CODER,
                ["task_2", "task_3"],
            ),
        ],
    )

    worker = create_orchestrator()

    results = await worker.execute(plan)

    assert set(results.keys()) == {
        "task_1",
        "task_2",
        "task_3",
        "task_4",
    }


@pytest.mark.asyncio
async def test_independent_tasks_run_concurrently() -> None:
    """
    Both tasks are independent and take 0.5 seconds.

    Sequential:
        ~1 second

    Concurrent:
        ~0.5 seconds
    """

    plan = Plan(
        objective="Test concurrency",
        assumptions=[],
        tasks=[
            create_task(
                "task_1",
                WorkerType.RESEARCHER,
            ),
            create_task(
                "task_2",
                WorkerType.CODER,
            ),
        ],
    )

    worker = create_orchestrator(
        delay=0.5,
    )

    start = time.perf_counter()

    await worker.execute(plan)

    elapsed = time.perf_counter() - start

    assert elapsed < 0.8


@pytest.mark.asyncio
async def test_dependent_tasks_do_not_run_concurrently() -> None:
    """
    task_2 depends on task_1.

    Each task takes 0.3 seconds, so execution
    should take approximately 0.6 seconds.
    """

    plan = Plan(
        objective="Test dependency ordering",
        assumptions=[],
        tasks=[
            create_task(
                "task_1",
                WorkerType.RESEARCHER,
            ),
            create_task(
                "task_2",
                WorkerType.CODER,
                ["task_1"],
            ),
        ],
    )

    worker = create_orchestrator(
        delay=0.3,
    )

    start = time.perf_counter()

    await worker.execute(plan)

    elapsed = time.perf_counter() - start

    assert elapsed >= 0.55


@pytest.mark.asyncio
async def test_branching_dag_executes_concurrent_wave() -> None:
    plan = Plan(
        objective="Test concurrent DAG execution",
        assumptions=[],
        tasks=[
            create_task(
                "task_1",
                WorkerType.RESEARCHER,
            ),
            create_task(
                "task_2",
                WorkerType.RESEARCHER,
                ["task_1"],
            ),
            create_task(
                "task_3",
                WorkerType.RESEARCHER,
                ["task_1"],
            ),
            create_task(
                "task_4",
                WorkerType.CODER,
                ["task_2", "task_3"],
            ),
        ],
    )

    worker = create_orchestrator(
        delay=0.3,
    )

    start = time.perf_counter()

    await worker.execute(plan)

    elapsed = time.perf_counter() - start

    assert elapsed < 1.1
