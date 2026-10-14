from pydantic import BaseModel, Field


class ReflectionResult(BaseModel):
    approved: bool = Field(description="Whether the draft satisfies the acceptance criteria.")
    feedback: str = Field(description="Specific feedback for improving the draft.")


class ReflectionAttempt(BaseModel):
    attempt: int = Field(ge=1)
    output: str
    reflection: ReflectionResult
