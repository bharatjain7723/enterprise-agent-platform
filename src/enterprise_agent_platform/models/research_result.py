from pydantic import BaseModel, Field

from enterprise_agent_platform.models.evidence import Evidence


class ResearchResult(BaseModel):
    question: str = Field(description="The question assigned to research")
    findings: list[str] = Field(min_length=1, description="The finding after research")
    assumptions: list[str] = Field(
        default_factory=list,
        description="The list of assumptions made while generating this result",
    )
    uncertainties: list[str] = Field(
        default_factory=list,
        description="The uncertainities in the mentioned questions and faced during research",
    )
    recommendations: list[str] = Field(
        default_factory=list, description="The recommendations from the research findings"
    )
    evidences: list[Evidence] = Field(
        default_factory=list, description="The evidences to support the findings"
    )
