import pytest

from enterprise_agent_platform.evaluation.deterministic import (
    DeterministicEvaluator,
)
from enterprise_agent_platform.evaluation.runner import EvaluationRunner
from enterprise_agent_platform.models.evaluation import EvaluationCase


@pytest.fixture
def runner() -> EvaluationRunner:
    return EvaluationRunner(DeterministicEvaluator())


def test_run_aggregates_results_and_metrics(
    runner: EvaluationRunner,
) -> None:
    cases = [
        EvaluationCase(
            id="case-1",
            input="Explain caching.",
            required_terms=["cache"],
        ),
        EvaluationCase(
            id="case-2",
            input="Explain Python.",
            required_terms=["python"],
        ),
        EvaluationCase(
            id="case-3",
            input="Explain databases.",
            required_terms=["database"],
        ),
    ]
    outputs = {
        "case-1": "A cache stores results.",
        "case-2": "This answer omits the required term.",
        "case-3": "A database stores information.",
    }

    results, summary = runner.run(cases, outputs)

    assert len(results) == 3
    assert [result.case_id for result in results] == [
        "case-1",
        "case-2",
        "case-3",
    ]
    assert summary.total_cases == 3
    assert summary.passed_cases == 2
    assert summary.failed_cases == 1
    assert summary.pass_rate == pytest.approx(2 / 3)
    assert summary.average_score == pytest.approx(2 / 3)


def test_run_handles_empty_dataset(
    runner: EvaluationRunner,
) -> None:
    results, summary = runner.run([], {})

    assert results == []
    assert summary.total_cases == 0
    assert summary.passed_cases == 0
    assert summary.failed_cases == 0
    assert summary.pass_rate == 0.0
    assert summary.average_score == 0.0


def test_run_rejects_missing_output(
    runner: EvaluationRunner,
) -> None:
    cases = [
        EvaluationCase(
            id="case-1",
            input="Explain caching.",
            required_terms=["cache"],
        )
    ]

    with pytest.raises(ValueError, match="Missing outputs"):
        runner.run(cases, {})


def test_run_rejects_duplicate_case_ids(
    runner: EvaluationRunner,
) -> None:
    cases = [
        EvaluationCase(id="duplicate", input="First question."),
        EvaluationCase(id="duplicate", input="Second question."),
    ]

    with pytest.raises(ValueError, match="IDs must be unique"):
        runner.run(cases, {"duplicate": "Some output."})
