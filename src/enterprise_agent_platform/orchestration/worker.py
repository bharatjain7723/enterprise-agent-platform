from pydantic import BaseModel

from enterprise_agent_platform.models.plan import Plan
from enterprise_agent_platform.models.task import Task
from enterprise_agent_platform.models.task_result import TaskResult
from enterprise_agent_platform.orchestration.registry import AgentRegistry


class WorkerOrchestrator:
    """Orchestrates the execution of tasks by the workers."""

    def __init__(self, registry: AgentRegistry) -> None:
        """Initializes the worker orchestrator."""
        self.registry = registry

    async def execute(
        self,
        plan: Plan,
    ) -> dict[str, TaskResult]:
        """Executes a plan of tasks."""
        results: dict[str, TaskResult] = {}
        for task in plan.tasks:
            results[task.id] = await self._execute_task(task, results)
        return results

    async def _execute_task(self, task: Task, results: dict[str, TaskResult]) -> TaskResult:
        """Executes a task after building the input based on its dependencies."""
        dependency_results = self._get_dependency_results(task, results)
        input_str = self._build_task_input(task, dependency_results)
        result = await self.registry.get(task.agent).run(input_str)
        return TaskResult(task=task, output=result)

    def _get_dependency_results(
        self,
        task: Task,
        results: dict[str, TaskResult],
    ) -> list[TaskResult]:
        dependency_results: list[TaskResult] = []

        for dependency_id in task.depends_on:
            if dependency_id not in results:
                raise ValueError(
                    f"Dependency '{dependency_id}' for task '{task.id}' has not been executed."
                )

            dependency_results.append(results[dependency_id])

        return dependency_results

    def _build_task_input(
        self,
        task: Task,
        dependency_results: list[TaskResult],
    ) -> str:
        """Build input for a worker using the task and dependency outputs."""

        sections = [
            "# Assigned Task",
            f"Task ID: {task.id}",
            f"Description: {task.description}",
        ]

        if dependency_results:
            sections.append("# Dependency Context")

            for result in dependency_results:
                output = (
                    result.output.model_dump_json(indent=2)
                    if isinstance(result.output, BaseModel)
                    else str(result.output)
                )

                sections.extend(
                    [
                        f"## Dependency: {result.task.id}",
                        f"Description: {result.task.description}",
                        f"Worker: {result.task.agent.value}",
                        "Output:",
                        output,
                    ]
                )

        return "\n\n".join(sections)
