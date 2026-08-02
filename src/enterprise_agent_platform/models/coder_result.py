from pydantic import BaseModel, Field

from enterprise_agent_platform.models.code_file import CodeFile


class CoderResult(BaseModel):
    summary: str = Field(description="The summary of the generated code and files")
    explanation: str = Field(
        description="An explanation of the code that has been written or modified"
    )
    assumptions: list[str] = Field(
        default_factory=list,
        description="Any assumptions which have been made during this coding task",
    )
    warnings: list[str] = Field(
        default_factory=list,
        description="Any warnings for the orchestrator or other agents from the generated code",
    )
    files: list[CodeFile] = Field(
        default_factory=list,
        description="List of the files which have been created or modified",
    )
