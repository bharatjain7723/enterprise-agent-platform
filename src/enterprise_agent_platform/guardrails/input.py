from enterprise_agent_platform.models.guardrail import GuardrailResult


class NonEmptyInputGuardrail:
    """Rejects input that is empty or contains only whitespace."""

    def check(self, user_input: str) -> GuardrailResult:
        if not user_input.strip():
            return GuardrailResult(
                allowed=False,
                guardrail_name="non_empty_input",
                reason="Input must not be empty or whitespace only.",
            )

        return GuardrailResult(
            allowed=True,
            guardrail_name="non_empty_input",
            reason="Input is not empty.",
        )


class MaxInputLengthGuardrail:
    """Rejects input longer than the configured character limit."""

    def __init__(self, max_length: int = 10_000) -> None:
        if max_length < 1:
            raise ValueError("max_length must be at least 1.")

        self._max_length = max_length

    def check(self, user_input: str) -> GuardrailResult:
        if len(user_input) > self._max_length:
            return GuardrailResult(
                allowed=False,
                guardrail_name="max_input_length",
                reason=(
                    f"Input length {len(user_input)} exceeds the "
                    f"maximum of {self._max_length} characters."
                ),
            )

        return GuardrailResult(
            allowed=True,
            guardrail_name="max_input_length",
            reason="Input is within the configured length limit.",
        )
