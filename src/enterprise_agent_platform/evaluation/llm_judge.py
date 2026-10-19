from typing import Protocol

from enterprise_agent_platform.agents.judge import JudgeAgent
from enterprise_agent_platform.models.evaluation import (
    EvaluationCase,
    EvaluationResult,
)
from enterprise_agent_platform.models.judge_assessment import JudgeAssessment


class JudgeRunner(Protocol):
    """Interface required by the LLM judge evaluator."""

    async def run(self, user_input: str) -> JudgeAssessment: ...


class LLMJudgeEvaluator:
    """Evaluates candidate answers using a structured LLM judgment."""

    def __init__(
        self,
        judge: JudgeRunner,
        *,
        pass_threshold: float = 0.8,
    ) -> None:
        if not 0.0 <= pass_threshold <= 1.0:
            raise ValueError("Pass threshold must be between 0.0 and 1.0.")

        self._judge = judge
        self._pass_threshold = pass_threshold

    @classmethod
    def from_agents_sdk(
        cls,
        *,
        model: str | None = None,
        pass_threshold: float = 0.8,
    ) -> "LLMJudgeEvaluator":
        """Construct the evaluator using the project's JudgeAgent."""
        judge = JudgeAgent(model=model)

        return cls(
            judge,
            pass_threshold=pass_threshold,
        )

    async def evaluate(
        self,
        case: EvaluationCase,
        output: str,
    ) -> EvaluationResult:
        prompt = (
            f"Question:\n{case.input}\n\n"
            f"Reference facts:\n{case.expected_facts}\n\n"
            f"Candidate answer:\n{output}\n\n"
            "Evaluate the candidate answer using the rubric."
        )

        assessment = await self._judge.run(prompt)

        score = (
            assessment.relevance + assessment.completeness + assessment.factual_consistency
        ) / 15.0

        passed = score >= self._pass_threshold and assessment.factual_consistency >= 3

        return EvaluationResult(
            case_id=case.id,
            passed=passed,
            score=score,
            feedback=assessment.feedback,
            missing_facts=[],
            missing_terms=[],
            relevance_score=assessment.relevance,
            completeness_score=assessment.completeness,
            factual_consistency_score=assessment.factual_consistency,
            issues=assessment.issues,
        )
