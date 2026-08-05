from typing import Any

from pydantic import BaseModel

from enterprise_agent_platform.models.task import Task


class TaskResult(BaseModel):
    task: Task
    output: Any
