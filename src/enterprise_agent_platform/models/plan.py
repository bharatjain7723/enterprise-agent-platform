from pydantic import BaseModel, Field

from enterprise_agent_platform.models.task import Task


class Plan(BaseModel):
    objective: str = Field(description="The objective defined from the user input")
    assumptions: list[str] = Field(
        description="The list of assumptions made while generating this plan"
    )
    tasks: list[Task] = Field(description="The list of tasks for other agents/user")
