from enterprise_agent_platform.models.plan import Plan


class PlanValidator:
    """Validates whether a plan can safely be executed."""

    def validate(self, plan: Plan) -> None:
        """
        Validate that the plan represents a valid dependency graph.

        Raises:
            ValueError: If the plan contains duplicate task IDs,
                missing dependencies, self-dependencies, or dependency cycles.
        """
        self._validate_unique_task_ids(plan)
        self._validate_dependencies_exist(plan)
        self._validate_no_self_dependencies(plan)
        self._validate_no_dependency_cycles(plan)

    def _validate_unique_task_ids(self, plan: Plan) -> None:
        """Validate that every task has a unique ID."""
        seen_ids: set[str] = set()

        for task in plan.tasks:
            if task.id in seen_ids:
                raise ValueError(f"Duplicate task ID found: '{task.id}'.")

            seen_ids.add(task.id)

    def _validate_dependencies_exist(self, plan: Plan) -> None:
        """Validate that every dependency references an existing task."""
        task_ids = {task.id for task in plan.tasks}

        for task in plan.tasks:
            for dependency_id in task.depends_on:
                if dependency_id not in task_ids:
                    raise ValueError(f"Task '{task.id}' depends on unknown task '{dependency_id}'.")

    def _validate_no_self_dependencies(self, plan: Plan) -> None:
        """Validate that a task does not depend on itself."""
        for task in plan.tasks:
            for dependency_id in task.depends_on:
                if dependency_id == task.id:
                    raise ValueError(f"Task '{task.id}' cannot depend on itself.")

    def _validate_no_dependency_cycles(self, plan: Plan) -> None:
        """Validate that the task dependency graph contains no cycles."""
        tasks_by_id = {task.id: task for task in plan.tasks}

        visiting: set[str] = set()
        visited: set[str] = set()

        def visit(task_id: str) -> None:
            # If we're already visiting this task, we've found a cycle.
            if task_id in visiting:
                raise ValueError(f"Dependency cycle detected involving task '{task_id}'.")

            # This task and all its dependencies have already been checked.
            if task_id in visited:
                return

            # Mark the task as part of the current DFS path.
            visiting.add(task_id)

            task = tasks_by_id[task_id]

            for dependency_id in task.depends_on:
                visit(dependency_id)

            # All dependencies are safe, so this task is fully processed.
            visiting.remove(task_id)
            visited.add(task_id)

        # The graph may contain multiple disconnected components,
        # so start DFS from every task that hasn't already been checked.
        for task in plan.tasks:
            visit(task.id)
