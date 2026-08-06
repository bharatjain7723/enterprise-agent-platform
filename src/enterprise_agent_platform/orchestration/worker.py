import asyncio

from pydantic import BaseModel

from enterprise_agent_platform.models.plan import Plan
from enterprise_agent_platform.models.task import Task
from enterprise_agent_platform.models.task_execution import TaskExecution
from enterprise_agent_platform.models.task_status import TaskStatus
from enterprise_agent_platform.orchestration.registry import AgentRegistry
from enterprise_agent_platform.orchestration.validator import PlanValidator


class WorkerOrchestrator:
    """Orchestrates the execution of tasks by the workers."""

    def __init__(
        self,
        registry: AgentRegistry,
        validator: PlanValidator,
    ) -> None:
        """Initializes the worker orchestrator."""
        self.registry = registry
        self.validator = validator

    async def execute(
        self,
        plan: Plan,
    ) -> dict[str, TaskExecution]:
        """Executes a plan of tasks."""

        self.validator.validate(plan)

        executions: dict[str, TaskExecution] = {
            task.id: TaskExecution(task=task) for task in plan.tasks
        }

        while self._has_pending_tasks(executions):
            self._mark_blocked_tasks(executions)

            if not self._has_pending_tasks(executions):
                break

            ready_to_execute_tasks = self._get_ready_tasks(executions)

            if not ready_to_execute_tasks:
                raise RuntimeError("No executable tasks found while tasks are still pending.")

            await asyncio.gather(
                *[
                    self._execute_task(
                        executions[task.id],
                        executions,
                    )
                    for task in ready_to_execute_tasks
                ]
            )

        return executions

    async def _execute_task(
        self,
        execution: TaskExecution,
        executions: dict[str, TaskExecution],
    ) -> None:
        """
        Execute a task and update its runtime state.

        Marks the task as COMPLETED on success
        or FAILED if execution raises an exception.
        """

        task = execution.task

        execution.status = TaskStatus.RUNNING
        execution.attempts += 1

        try:
            dependency_executions = self._get_dependency_executions(task, executions)
            input_str = self._build_task_input(task, dependency_executions)
            result = await self.registry.get(task.agent).run(input_str)

            execution.output = result
            execution.status = TaskStatus.COMPLETED
            execution.error = None
        except Exception as exc:
            execution.status = TaskStatus.FAILED
            execution.error = str(exc)

    def _get_dependency_executions(
        self,
        task: Task,
        executions: dict[str, TaskExecution],
    ) -> list[TaskExecution]:
        dependency_executions: list[TaskExecution] = []

        for dependency_id in task.depends_on:
            dependency_execution = executions[dependency_id]
            if dependency_execution.status != TaskStatus.COMPLETED:
                raise RuntimeError(
                    f"Dependency '{dependency_id}' for task '{task.id}' "
                    f"is not completed. Current status: "
                    f"'{dependency_execution.status.value}'."
                )

            dependency_executions.append(dependency_execution)

        return dependency_executions

    def _build_task_input(
        self,
        task: Task,
        dependency_executions: list[TaskExecution],
    ) -> str:
        """Build input for a worker using the task and dependency outputs."""

        sections = [
            "# Assigned Task",
            f"Task ID: {task.id}",
            f"Description: {task.description}",
        ]

        if dependency_executions:
            sections.append("# Dependency Context")

            for execution in dependency_executions:
                output = (
                    execution.output.model_dump_json(indent=2)
                    if isinstance(execution.output, BaseModel)
                    else str(execution.output)
                )

                sections.extend(
                    [
                        f"## Dependency: {execution.task.id}",
                        f"Description: {execution.task.description}",
                        f"Worker: {execution.task.agent.value}",
                        "Output:",
                        output,
                    ]
                )

        return "\n\n".join(sections)

    def _get_ready_tasks(
        self,
        executions: dict[str, TaskExecution],
    ) -> list[Task]:
        """Return tasks whose dependencies have all completed."""

        ready_tasks: list[Task] = []

        for execution in executions.values():
            if execution.status != TaskStatus.PENDING:
                continue

            task = execution.task

            if all(
                executions[dependency_id].status == TaskStatus.COMPLETED
                for dependency_id in task.depends_on
            ):
                ready_tasks.append(task)

        return ready_tasks

    def _has_pending_tasks(
        self,
        executions: dict[str, TaskExecution],
    ) -> bool:
        return any(execution.status == TaskStatus.PENDING for execution in executions.values())

    def _mark_blocked_tasks(
        self,
        executions: dict[str, TaskExecution],
    ) -> None:
        """Mark tasks as blocked when any dependency has failed or is blocked."""

        def check_and_mark_blocked(
            execution: TaskExecution,
        ) -> bool:
            """
            Recursively check whether a task should be blocked.

            Returns True if the task is blocked, otherwise False.
            """

            # A failed or already-blocked task prevents its dependents from running.
            if execution.status in {
                TaskStatus.FAILED,
                TaskStatus.BLOCKED,
            }:
                return True

            # Completed and RUNNING tasks are healthy dependencies.
            if execution.status in {
                TaskStatus.COMPLETED,
                TaskStatus.RUNNING,
            }:
                return False

            task = execution.task

            for dependency_id in task.depends_on:
                dependency_execution = executions[dependency_id]

                dependency_prevents_execution = check_and_mark_blocked(dependency_execution)

                if dependency_prevents_execution:
                    execution.status = TaskStatus.BLOCKED
                    execution.error = (
                        f"Task blocked because dependency '{dependency_id}' failed or was blocked."
                    )

                    return True

            return False

        for execution in executions.values():
            if execution.status == TaskStatus.PENDING:
                check_and_mark_blocked(execution)
