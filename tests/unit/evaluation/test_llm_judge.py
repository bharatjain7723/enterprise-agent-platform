import pytest

from enterprise_agent_platform.evaluation.llm_judge import (
    LLMJudgeEvaluator,
)
from enterprise_agent_platform.models.evaluation import EvaluationCase
from enterprise_agent_platform.models.judge_assessment import JudgeAssessment


class FakeJudge:
    """Returns a fixed assessment without calling an LLM."""

    def __init__(self, assessment: JudgeAssessment) -> None:
        self.assessment = assessment
        self.last_input: str | None = None

    async def run(self, user_input: str) -> JudgeAssessment:
        self.last_input = user_input
        return self.assessment


@pytest.fixture
def case() -> EvaluationCase:
    return EvaluationCase(
        id="judge-001",
        input="Explain caching.",
        expected_facts=[
            "Caching stores results for reuse.",
            "Repeated calls can reuse cached results.",
        ],
    )


@pytest.mark.asyncio
async def test_evaluate_passes_high_quality_answer(
    case: EvaluationCase,
) -> None:
    fake_judge = FakeJudge(
        JudgeAssessment(
            relevance=5,
            completeness=4,
            factual_consistency=5,
            feedback="Accurate and complete.",
        )
    )
    evaluator = LLMJudgeEvaluator(fake_judge)

    result = await evaluator.evaluate(
        case,
        "Caching stores results for reuse.",
    )

    assert result.case_id == "judge-001"
    assert result.passed is True
    assert result.score == pytest.approx(14 / 15)
    assert result.feedback == "Accurate and complete."
    assert fake_judge.last_input is not None
    assert "Caching stores results for reuse." in fake_judge.last_input
    assert "Reference facts" in fake_judge.last_input


@pytest.mark.asyncio
async def test_evaluate_fails_low_quality_answer(
    case: EvaluationCase,
) -> None:
    fake_judge = FakeJudge(
        JudgeAssessment(
            relevance=2,
            completeness=1,
            factual_consistency=2,
            feedback="The answer misses the key concepts.",
            issues=["Missing core explanation"],
        )
    )
    evaluator = LLMJudgeEvaluator(fake_judge)

    result = await evaluator.evaluate(case, "It is useful.")

    assert result.passed is False
    assert result.score == pytest.approx(5 / 15)
    assert result.feedback == "The answer misses the key concepts."


@pytest.mark.asyncio
async def test_factual_consistency_can_block_a_pass(
    case: EvaluationCase,
) -> None:
    fake_judge = FakeJudge(
        JudgeAssessment(
            relevance=5,
            completeness=5,
            factual_consistency=2,
            feedback="The answer contradicts the reference.",
        )
    )
    evaluator = LLMJudgeEvaluator(fake_judge, pass_threshold=0.8)

    result = await evaluator.evaluate(case, "A contradictory answer.")

    assert result.score == pytest.approx(12 / 15)
    assert result.passed is False


def test_rejects_invalid_pass_threshold() -> None:
    fake_judge = FakeJudge(
        JudgeAssessment(
            relevance=5,
            completeness=5,
            factual_consistency=5,
            feedback="Good.",
        )
    )

    with pytest.raises(ValueError, match="Pass threshold"):
        LLMJudgeEvaluator(fake_judge, pass_threshold=1.1)
