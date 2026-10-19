from pydantic import BaseModel, Field


class EvaluationCase(BaseModel):
    """A single test example used to evaluate an agent."""

    id: str = Field(min_length=1)
    input: str = Field(min_length=1)
    expected_facts: list[str] = Field(default_factory=list)
    required_terms: list[str] = Field(default_factory=list)


class EvaluationResult(BaseModel):
    """The evaluation outcome for one test case."""

    case_id: str = Field(min_length=1)
    passed: bool
    score: float = Field(ge=0.0, le=1.0)
    missing_facts: list[str] = Field(default_factory=list)
    missing_terms: list[str] = Field(default_factory=list)
    feedback: str = ""
    relevance_score: int | None = Field(default=None, ge=1, le=5)
    completeness_score: int | None = Field(default=None, ge=1, le=5)
    factual_consistency_score: int | None = Field(default=None, ge=1, le=5)
    issues: list[str] = Field(default_factory=list)


class EvaluationSummary(BaseModel):
    """Aggregate metrics from evaluating a dataset."""

    total_cases: int = Field(ge=0)
    passed_cases: int = Field(ge=0)
    failed_cases: int = Field(ge=0)
    pass_rate: float = Field(ge=0.0, le=1.0)
    average_score: float = Field(ge=0.0, le=1.0)
