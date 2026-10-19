from enterprise_agent_platform.models.evaluation import (
    EvaluationCase,
    EvaluationResult,
)


class DeterministicEvaluator:
    """Evaluates an answer using explicit text-matching criteria."""

    def evaluate(
        self,
        case: EvaluationCase,
        output: str,
    ) -> EvaluationResult:
        normalized_output = output.casefold()

        missing_terms = [
            term for term in case.required_terms if term.casefold() not in normalized_output
        ]

        # This initial implementation treats each expected fact as a
        # required literal phrase. It does not perform semantic matching.
        missing_facts = [
            fact for fact in case.expected_facts if fact.casefold() not in normalized_output
        ]

        total_checks = len(case.required_terms) + len(case.expected_facts)
        passed_checks = total_checks - len(missing_terms) - len(missing_facts)

        # With no configured checks, the evaluator has no evidence of
        # correctness, so it returns a neutral score and a failed result.
        score = passed_checks / total_checks if total_checks else 0.0
        passed = total_checks > 0 and passed_checks == total_checks

        feedback_parts: list[str] = []

        if missing_terms:
            feedback_parts.append(f"Missing required terms: {', '.join(missing_terms)}.")

        if missing_facts:
            feedback_parts.append(f"Missing expected facts: {', '.join(missing_facts)}.")

        if total_checks == 0:
            feedback_parts.append("No evaluation criteria were configured.")
        elif passed:
            feedback_parts.append("All configured checks passed.")

        return EvaluationResult(
            case_id=case.id,
            passed=passed,
            score=score,
            missing_facts=missing_facts,
            missing_terms=missing_terms,
            feedback=" ".join(feedback_parts),
        )
