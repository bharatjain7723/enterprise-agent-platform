from pydantic import BaseModel, Field

from enterprise_agent_platform.models.worker_type import WorkerType


class Task(BaseModel):
    id: str = Field(description="The id of the task")
    description: str = Field(description="The description of this specific task")
    agent: WorkerType = Field(description="The type of the agent")
    depends_on: list[str] = Field(
        description="The list of agents this task depends on.", default_factory=list
    )
