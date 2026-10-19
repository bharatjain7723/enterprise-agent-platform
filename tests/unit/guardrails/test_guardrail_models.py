import pytest
from pydantic import ValidationError

from enterprise_agent_platform.models.guardrail import GuardrailResult


def test_guardrail_result_allows_request() -> None:
    result = GuardrailResult(
        allowed=True,
        guardrail_name="non_empty_input",
        reason="Input is valid.",
    )

    assert result.allowed is True
    assert result.guardrail_name == "non_empty_input"
    assert result.reason == "Input is valid."


def test_guardrail_result_representing_rejection() -> None:
    result = GuardrailResult(
        allowed=False,
        guardrail_name="max_input_length",
        reason="Input exceeds the limit.",
    )

    assert result.allowed is False


def test_guardrail_name_must_not_be_empty() -> None:
    with pytest.raises(ValidationError):
        GuardrailResult(
            allowed=False,
            guardrail_name="",
        )
