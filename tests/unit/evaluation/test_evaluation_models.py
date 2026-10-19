import pytest
from pydantic import ValidationError

from enterprise_agent_platform.models.evaluation import (
    EvaluationCase,
    EvaluationResult,
    EvaluationSummary,
)


def test_evaluation_case_uses_empty_lists_by_default() -> None:
    case = EvaluationCase(
        id="case-1",
        input="Explain caching.",
    )

    assert case.expected_facts == []
    assert case.required_terms == []


def test_evaluation_case_rejects_empty_id() -> None:
    with pytest.raises(ValidationError):
        EvaluationCase(id="", input="Explain caching.")


def test_evaluation_result_accepts_valid_score() -> None:
    result = EvaluationResult(
        case_id="case-1",
        passed=True,
        score=1.0,
        feedback="All checks passed.",
    )

    assert result.passed is True
    assert result.score == 1.0
    assert result.missing_facts == []
    assert result.missing_terms == []


@pytest.mark.parametrize("score", [-0.1, 1.1])
def test_evaluation_result_rejects_out_of_range_score(
    score: float,
) -> None:
    with pytest.raises(ValidationError):
        EvaluationResult(
            case_id="case-1",
            passed=False,
            score=score,
        )


def test_evaluation_summary_accepts_valid_metrics() -> None:
    summary = EvaluationSummary(
        total_cases=10,
        passed_cases=8,
        failed_cases=2,
        pass_rate=0.8,
        average_score=0.85,
    )

    assert summary.total_cases == 10
    assert summary.passed_cases == 8
    assert summary.failed_cases == 2
    assert summary.pass_rate == 0.8
