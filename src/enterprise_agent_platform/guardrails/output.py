from enterprise_agent_platform.models.guardrail import GuardrailResult


class NonEmptyOutputGuardrail:
    """Rejects missing or blank textual agent output."""

    def check(self, output: object) -> GuardrailResult:
        if output is None:
            return GuardrailResult(
                allowed=False,
                guardrail_name="non_empty_output",
                reason="Agent output must not be None.",
            )

        if isinstance(output, str) and not output.strip():
            return GuardrailResult(
                allowed=False,
                guardrail_name="non_empty_output",
                reason="Agent output must not be empty or whitespace only.",
            )

        return GuardrailResult(
            allowed=True,
            guardrail_name="non_empty_output",
            reason="Agent output passed the non-empty check.",
        )
