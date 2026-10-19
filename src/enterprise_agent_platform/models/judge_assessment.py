from pydantic import BaseModel, Field


class JudgeAssessment(BaseModel):
    """Structured evaluation produced by an LLM judge."""

    relevance: int = Field(ge=1, le=5)
    completeness: int = Field(ge=1, le=5)
    factual_consistency: int = Field(ge=1, le=5)
    feedback: str
    issues: list[str] = Field(default_factory=list)
