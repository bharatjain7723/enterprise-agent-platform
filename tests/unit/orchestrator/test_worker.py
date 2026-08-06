import asyncio
import time

import pytest
from pydantic import BaseModel

from enterprise_agent_platform.exceptions import NonRetryableError, RetryableError
from enterprise_agent_platform.models.plan import Plan
from enterprise_agent_platform.models.task import Task
from enterprise_agent_platform.models.task_status import TaskStatus
from enterprise_agent_platform.models.worker_type import WorkerType
from enterprise_agent_platform.orchestration.registry import AgentRegistry
from enterprise_agent_platform.orchestration.retry import RetryPolicy
from enterprise_agent_platform.orchestration.validator import PlanValidator
from enterprise_agent_platform.orchestration.worker import WorkerOrchestrator


class FakeResult(BaseModel):
    message: str


class FakeAgent:
    """Fake agent used to test orchestration without calling an LLM."""

    def __init__(
        self,
        name: str,
        delay: float = 0.0,
        should_fail: bool = False,
        fail_attempts: int = 0,
        error: Exception | None = None,
    ) -> None:
        self.name = name
        self.delay = delay
        self.should_fail = should_fail
        self.fail_attempts = fail_attempts
        self.error = error
        self.call_count = 0

    async def run(
        self,
        user_input: str,
    ) -> FakeResult:
        self.call_count += 1

        if self.delay:
            await asyncio.sleep(self.delay)

        if self.should_fail:
            raise RuntimeError(f"{self.name} intentionally failed.")

        if self.call_count <= self.fail_attempts:
            if self.error is not None:
                raise self.error

            raise RuntimeError(f"{self.name} failed on attempt {self.call_count}.")

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
        retry_policy=RetryPolicy(
            max_attempts=1,
            base_delay_seconds=0,
            jitter_seconds=0,
        ),
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

    executions = await worker.execute(plan)

    assert len(executions) == 2
    assert "task_1" in executions
    assert "task_2" in executions

    if isinstance(executions["task_1"].output, FakeResult):
        assert executions["task_1"].output.message == "Fake Researcher completed task."

    if isinstance(executions["task_2"].output, FakeResult):
        assert executions["task_2"].output.message == "Fake Coder completed task."


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

    executions = await worker.execute(plan)

    assert set(executions.keys()) == {
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


@pytest.mark.asyncio
async def test_failed_task_is_marked_failed() -> None:
    registry = AgentRegistry()

    registry.register(
        WorkerType.RESEARCHER,
        FakeAgent(
            name="Fake Researcher",
            should_fail=True,
        ),
    )

    worker = WorkerOrchestrator(
        registry=registry,
        validator=PlanValidator(),
        retry_policy=RetryPolicy(
            max_attempts=1,
            base_delay_seconds=0,
            jitter_seconds=0,
        ),
    )

    plan = Plan(
        objective="Test task failure",
        assumptions=[],
        tasks=[
            create_task(
                "task_1",
                WorkerType.RESEARCHER,
            ),
        ],
    )

    executions = await worker.execute(plan)

    execution = executions["task_1"]

    assert execution.status == TaskStatus.FAILED
    assert execution.output is None
    assert execution.attempts == 1
    assert execution.error == "Fake Researcher intentionally failed."


@pytest.mark.asyncio
async def test_dependent_task_is_blocked_when_dependency_fails() -> None:
    registry = AgentRegistry()

    registry.register(
        WorkerType.RESEARCHER,
        FakeAgent(
            name="Fake Researcher",
            should_fail=True,
        ),
    )

    registry.register(
        WorkerType.CODER,
        FakeAgent(
            name="Fake Coder",
        ),
    )

    worker = WorkerOrchestrator(
        registry=registry,
        validator=PlanValidator(),
        retry_policy=RetryPolicy(
            max_attempts=1,
            base_delay_seconds=0,
            jitter_seconds=0,
        ),
    )

    plan = Plan(
        objective="Test blocked dependency",
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

    executions = await worker.execute(plan)

    assert executions["task_1"].status == TaskStatus.FAILED

    assert executions["task_2"].status == TaskStatus.BLOCKED

    assert executions["task_2"].attempts == 0
    assert executions["task_2"].output is None
    assert executions["task_2"].error is not None


@pytest.mark.asyncio
async def test_blocking_propagates_through_dependency_chain() -> None:
    registry = AgentRegistry()

    registry.register(
        WorkerType.RESEARCHER,
        FakeAgent(
            name="Fake Researcher",
            should_fail=True,
        ),
    )

    registry.register(
        WorkerType.CODER,
        FakeAgent(
            name="Fake Coder",
        ),
    )

    worker = WorkerOrchestrator(
        registry=registry,
        validator=PlanValidator(),
        retry_policy=RetryPolicy(
            max_attempts=1,
            base_delay_seconds=0,
            jitter_seconds=0,
        ),
    )

    plan = Plan(
        objective="Test transitive blocking",
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
            create_task(
                "task_3",
                WorkerType.CODER,
                ["task_2"],
            ),
            create_task(
                "task_4",
                WorkerType.CODER,
                ["task_3"],
            ),
        ],
    )

    executions = await worker.execute(plan)

    assert executions["task_1"].status == TaskStatus.FAILED
    assert executions["task_2"].status == TaskStatus.BLOCKED
    assert executions["task_3"].status == TaskStatus.BLOCKED
    assert executions["task_4"].status == TaskStatus.BLOCKED

    assert executions["task_1"].attempts == 1
    assert executions["task_2"].attempts == 0
    assert executions["task_3"].attempts == 0
    assert executions["task_4"].attempts == 0


@pytest.mark.asyncio
async def test_independent_branch_continues_after_failure() -> None:
    registry = AgentRegistry()

    registry.register(
        WorkerType.RESEARCHER,
        FakeAgent(
            name="Fake Researcher",
            should_fail=True,
        ),
    )

    registry.register(
        WorkerType.CODER,
        FakeAgent(
            name="Fake Coder",
        ),
    )

    worker = WorkerOrchestrator(
        registry=registry,
        validator=PlanValidator(),
        retry_policy=RetryPolicy(
            max_attempts=1,
            base_delay_seconds=0,
            jitter_seconds=0,
        ),
    )

    plan = Plan(
        objective="Test independent branch failure",
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
            create_task(
                "task_3",
                WorkerType.CODER,
            ),
            create_task(
                "task_4",
                WorkerType.CODER,
                ["task_3"],
            ),
        ],
    )

    executions = await worker.execute(plan)

    assert executions["task_1"].status == TaskStatus.FAILED
    assert executions["task_2"].status == TaskStatus.BLOCKED

    assert executions["task_3"].status == TaskStatus.COMPLETED
    assert executions["task_4"].status == TaskStatus.COMPLETED


@pytest.mark.asyncio
async def test_task_succeeds_on_first_attempt() -> None:
    agent = FakeAgent(
        name="Fake Researcher",
        fail_attempts=0,
    )

    registry = AgentRegistry()
    registry.register(
        WorkerType.RESEARCHER,
        agent,
    )

    worker = WorkerOrchestrator(
        registry=registry,
        validator=PlanValidator(),
        retry_policy=RetryPolicy(
            max_attempts=3,
            base_delay_seconds=0,
            jitter_seconds=0,
        ),
    )

    plan = Plan(
        objective="Test immediate success",
        assumptions=[],
        tasks=[
            create_task(
                "task_1",
                WorkerType.RESEARCHER,
            ),
        ],
    )

    executions = await worker.execute(plan)

    execution = executions["task_1"]

    assert execution.status == TaskStatus.COMPLETED
    assert execution.attempts == 1
    assert execution.error is None
    assert agent.call_count == 1


@pytest.mark.asyncio
async def test_task_retries_after_failure() -> None:
    agent = FakeAgent(
        name="Fake Researcher",
        fail_attempts=1,
        error=RetryableError("Temporary service failure"),
    )

    registry = AgentRegistry()
    registry.register(
        WorkerType.RESEARCHER,
        agent,
    )

    worker = WorkerOrchestrator(
        registry=registry,
        validator=PlanValidator(),
        retry_policy=RetryPolicy(
            max_attempts=3,
            base_delay_seconds=0,
            jitter_seconds=0,
        ),
    )

    plan = Plan(
        objective="Test retry",
        assumptions=[],
        tasks=[
            create_task(
                "task_1",
                WorkerType.RESEARCHER,
            ),
        ],
    )

    executions = await worker.execute(plan)

    execution = executions["task_1"]

    assert execution.status == TaskStatus.COMPLETED
    assert execution.attempts == 2
    assert execution.error is None
    assert agent.call_count == 2


@pytest.mark.asyncio
async def test_task_succeeds_on_final_attempt() -> None:
    agent = FakeAgent(
        name="Fake Researcher",
        fail_attempts=2,
        error=RetryableError("Temporary service failure"),
    )

    registry = AgentRegistry()
    registry.register(
        WorkerType.RESEARCHER,
        agent,
    )

    worker = WorkerOrchestrator(
        registry=registry,
        validator=PlanValidator(),
        retry_policy=RetryPolicy(
            max_attempts=3,
            base_delay_seconds=0,
            jitter_seconds=0,
        ),
    )

    plan = Plan(
        objective="Test final retry success",
        assumptions=[],
        tasks=[
            create_task(
                "task_1",
                WorkerType.RESEARCHER,
            ),
        ],
    )

    executions = await worker.execute(plan)

    execution = executions["task_1"]

    assert execution.status == TaskStatus.COMPLETED
    assert execution.attempts == 3
    assert execution.error is None
    assert agent.call_count == 3


@pytest.mark.asyncio
async def test_task_fails_after_max_attempts() -> None:
    agent = FakeAgent(
        name="Fake Researcher",
        fail_attempts=100,
        error=RetryableError("Temporary service failure"),
    )

    registry = AgentRegistry()
    registry.register(
        WorkerType.RESEARCHER,
        agent,
    )

    worker = WorkerOrchestrator(
        registry=registry,
        validator=PlanValidator(),
        retry_policy=RetryPolicy(
            max_attempts=3,
            base_delay_seconds=0,
            jitter_seconds=0,
        ),
    )

    plan = Plan(
        objective="Test retry exhaustion",
        assumptions=[],
        tasks=[
            create_task(
                "task_1",
                WorkerType.RESEARCHER,
            ),
        ],
    )

    executions = await worker.execute(plan)

    execution = executions["task_1"]

    assert execution.status == TaskStatus.FAILED
    assert execution.attempts == 3
    assert agent.call_count == 3
    assert execution.error is not None


@pytest.mark.asyncio
async def test_task_retries_after_failure_retryable_error() -> None:
    agent = FakeAgent(
        name="Fake Researcher",
        fail_attempts=2,
        error=RetryableError("Temporary service failure"),
    )

    registry = AgentRegistry()
    registry.register(
        WorkerType.RESEARCHER,
        agent,
    )

    worker = WorkerOrchestrator(
        registry=registry,
        validator=PlanValidator(),
        retry_policy=RetryPolicy(
            max_attempts=3,
            base_delay_seconds=0,
            jitter_seconds=0,
        ),
    )

    plan = Plan(
        objective="Test retry",
        assumptions=[],
        tasks=[
            create_task(
                "task_1",
                WorkerType.RESEARCHER,
            ),
        ],
    )

    executions = await worker.execute(plan)

    execution = executions["task_1"]

    assert execution.status == TaskStatus.COMPLETED
    assert execution.attempts == 3
    assert execution.error is None
    assert agent.call_count == 3


@pytest.mark.asyncio
async def test_task_retries_after_failure_non_retryable_error() -> None:
    agent = FakeAgent(
        name="Fake Researcher",
        fail_attempts=2,
        error=NonRetryableError("Invalid configuration"),
    )

    registry = AgentRegistry()
    registry.register(
        WorkerType.RESEARCHER,
        agent,
    )

    worker = WorkerOrchestrator(
        registry=registry,
        validator=PlanValidator(),
        retry_policy=RetryPolicy(
            max_attempts=3,
            base_delay_seconds=0,
            jitter_seconds=0,
        ),
    )

    plan = Plan(
        objective="Test retry",
        assumptions=[],
        tasks=[
            create_task(
                "task_1",
                WorkerType.RESEARCHER,
            ),
        ],
    )

    executions = await worker.execute(plan)

    execution = executions["task_1"]

    assert execution.status == TaskStatus.FAILED
    assert execution.attempts == 1
    assert execution.error == "Invalid configuration"
    assert agent.call_count == 1
