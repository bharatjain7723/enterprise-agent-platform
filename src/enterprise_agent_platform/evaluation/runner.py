from enterprise_agent_platform.evaluation.deterministic import (
    DeterministicEvaluator,
)
from enterprise_agent_platform.models.evaluation import (
    EvaluationCase,
    EvaluationResult,
    EvaluationSummary,
)


class EvaluationRunner:
    """Runs an evaluator across a dataset of cases and outputs."""

    def __init__(self, evaluator: DeterministicEvaluator) -> None:
        self._evaluator = evaluator

    def run(
        self,
        cases: list[EvaluationCase],
        outputs: dict[str, str],
    ) -> tuple[list[EvaluationResult], EvaluationSummary]:
        case_ids = [case.id for case in cases]
        if len(case_ids) != len(set(case_ids)):
            raise ValueError("Evaluation case IDs must be unique.")

        missing_outputs = [case_id for case_id in case_ids if case_id not in outputs]
        if missing_outputs:
            raise ValueError(f"Missing outputs for evaluation cases: {', '.join(missing_outputs)}.")

        results = [self._evaluator.evaluate(case, outputs[case.id]) for case in cases]

        total = len(results)
        passed = sum(result.passed for result in results)
        failed = total - passed

        summary = EvaluationSummary(
            total_cases=total,
            passed_cases=passed,
            failed_cases=failed,
            pass_rate=passed / total if total else 0.0,
            average_score=(sum(result.score for result in results) / total if total else 0.0),
        )

        return results, summary
