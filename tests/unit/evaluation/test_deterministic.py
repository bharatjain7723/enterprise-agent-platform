import pytest

from enterprise_agent_platform.evaluation.deterministic import (
    DeterministicEvaluator,
)
from enterprise_agent_platform.models.evaluation import EvaluationCase


@pytest.fixture
def evaluator() -> DeterministicEvaluator:
    return DeterministicEvaluator()


def test_passes_when_all_checks_match(
    evaluator: DeterministicEvaluator,
) -> None:
    case = EvaluationCase(
        id="cache-001",
        input="Explain caching.",
        expected_facts=["caches function results"],
        required_terms=["cache", "python"],
    )

    result = evaluator.evaluate(
        case,
        "Python uses a cache that caches function results.",
    )

    assert result.passed is True
    assert result.score == 1.0
    assert result.missing_facts == []
    assert result.missing_terms == []
    assert "All configured checks passed." in result.feedback


def test_matching_is_case_insensitive(
    evaluator: DeterministicEvaluator,
) -> None:
    case = EvaluationCase(
        id="cache-002",
        input="Explain caching.",
        required_terms=["PYTHON", "CACHE"],
    )

    result = evaluator.evaluate(case, "Python uses a cache.")

    assert result.passed is True
    assert result.score == 1.0


def test_reports_missing_terms_and_facts(
    evaluator: DeterministicEvaluator,
) -> None:
    case = EvaluationCase(
        id="cache-003",
        input="Explain caching.",
        expected_facts=[
            "caches function results",
            "supports a maximum size",
        ],
        required_terms=["python", "cache"],
    )

    result = evaluator.evaluate(
        case,
        "Python uses a cache that caches function results.",
    )

    assert result.passed is False
    assert result.score == 0.75
    assert result.missing_facts == ["supports a maximum size"]
    assert result.missing_terms == []
    assert "supports a maximum size" in result.feedback


def test_fails_when_all_checks_are_missing(
    evaluator: DeterministicEvaluator,
) -> None:
    case = EvaluationCase(
        id="cache-004",
        input="Explain caching.",
        expected_facts=["stores results"],
        required_terms=["python"],
    )

    result = evaluator.evaluate(case, "This is an unrelated answer.")

    assert result.passed is False
    assert result.score == 0.0
    assert result.missing_facts == ["stores results"]
    assert result.missing_terms == ["python"]


def test_empty_criteria_fail_with_neutral_score(
    evaluator: DeterministicEvaluator,
) -> None:
    case = EvaluationCase(
        id="cache-005",
        input="Explain caching.",
    )

    result = evaluator.evaluate(case, "Any answer.")

    assert result.passed is False
    assert result.score == 0.0
    assert "No evaluation criteria were configured." in result.feedback


@pytest.mark.parametrize(
    ("output", "expected_score"),
    [
        ("python cache", 1.0),
        ("python only", 0.5),
        ("cache only", 0.5),
        ("neither term", 0.0),
    ],
)
def test_score_reflects_fraction_of_checks_passed(
    evaluator: DeterministicEvaluator,
    output: str,
    expected_score: float,
) -> None:
    case = EvaluationCase(
        id="cache-006",
        input="Explain caching.",
        required_terms=["python", "cache"],
    )

    result = evaluator.evaluate(case, output)

    assert result.score == expected_score
