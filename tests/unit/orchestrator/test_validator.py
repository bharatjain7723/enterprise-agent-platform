import pytest

from enterprise_agent_platform.models.plan import Plan
from enterprise_agent_platform.models.task import Task
from enterprise_agent_platform.models.worker_type import WorkerType
from enterprise_agent_platform.orchestration.validator import PlanValidator


def create_task(
    task_id: str,
    depends_on: list[str] | None = None,
) -> Task:
    """Helper for creating tasks used in validator tests."""
    return Task(
        id=task_id,
        description=f"Test task {task_id}",
        agent=WorkerType.RESEARCHER,
        depends_on=depends_on or [],
    )


def create_plan(tasks: list[Task]) -> Plan:
    """Helper for creating plans used in validator tests."""
    return Plan(
        objective="Test objective",
        assumptions=[],
        tasks=tasks,
    )


def test_valid_plan() -> None:
    plan = create_plan(
        [
            create_task("task_1"),
            create_task("task_2", ["task_1"]),
            create_task("task_3", ["task_2"]),
        ]
    )

    validator = PlanValidator()

    # Should complete without raising an exception.
    validator.validate(plan)


def test_valid_branching_plan() -> None:
    """
      task_1
      //  \\
     v      v
    task_2 task_3
      \\    //
       v    v
       task_4
    """
    plan = create_plan(
        [
            create_task("task_1"),
            create_task("task_2", ["task_1"]),
            create_task("task_3", ["task_1"]),
            create_task("task_4", ["task_2", "task_3"]),
        ]
    )

    validator = PlanValidator()

    validator.validate(plan)


def test_duplicate_task_ids() -> None:
    plan = create_plan(
        [
            create_task("task_1"),
            create_task("task_1"),
        ]
    )

    validator = PlanValidator()

    with pytest.raises(
        ValueError,
        match="Duplicate task ID",
    ):
        validator.validate(plan)


def test_missing_dependency() -> None:
    plan = create_plan(
        [
            create_task("task_1"),
            create_task("task_2", ["task_999"]),
        ]
    )

    validator = PlanValidator()

    with pytest.raises(
        ValueError,
        match="depends on unknown task",
    ):
        validator.validate(plan)


def test_self_dependency() -> None:
    plan = create_plan(
        [
            create_task("task_1", ["task_1"]),
        ]
    )

    validator = PlanValidator()

    with pytest.raises(
        ValueError,
        match="cannot depend on itself",
    ):
        validator.validate(plan)


def test_direct_dependency_cycle() -> None:
    """
    task_1 <--> task_2
    """
    plan = create_plan(
        [
            create_task("task_1", ["task_2"]),
            create_task("task_2", ["task_1"]),
        ]
    )

    validator = PlanValidator()

    with pytest.raises(
        ValueError,
        match="Dependency cycle detected",
    ):
        validator.validate(plan)


def test_indirect_dependency_cycle() -> None:
    """
    task_1 -> task_2 -> task_3
       ^                  |
       |__________________|
    """
    plan = create_plan(
        [
            create_task("task_1", ["task_3"]),
            create_task("task_2", ["task_1"]),
            create_task("task_3", ["task_2"]),
        ]
    )

    validator = PlanValidator()

    with pytest.raises(
        ValueError,
        match="Dependency cycle detected",
    ):
        validator.validate(plan)
