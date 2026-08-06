from typing import Any

from pydantic import BaseModel, Field

from enterprise_agent_platform.models.task import Task
from enterprise_agent_platform.models.task_status import TaskStatus


class TaskExecution(BaseModel):
    """Runtime execution state for a task."""

    task: Task

    status: TaskStatus = TaskStatus.PENDING

    output: Any | None = None

    error: str | None = None

    attempts: int = Field(
        default=0,
        ge=0,
    )
