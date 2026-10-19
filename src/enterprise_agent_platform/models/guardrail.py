from pydantic import BaseModel, Field


class GuardrailResult(BaseModel):
    """Outcome of running one guardrail check."""

    allowed: bool
    guardrail_name: str = Field(min_length=1)
    reason: str = ""
