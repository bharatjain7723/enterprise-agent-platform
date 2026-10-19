import pytest

from enterprise_agent_platform.guardrails.output import (
    NonEmptyOutputGuardrail,
)


def test_non_empty_output_guardrail_allows_text() -> None:
    result = NonEmptyOutputGuardrail().check("Here is the answer.")

    assert result.allowed is True


@pytest.mark.parametrize("output", ["", " ", "\n\t"])
def test_non_empty_output_guardrail_rejects_blank_text(
    output: str,
) -> None:
    result = NonEmptyOutputGuardrail().check(output)

    assert result.allowed is False
    assert "must not be empty" in result.reason


def test_non_empty_output_guardrail_rejects_none() -> None:
    result = NonEmptyOutputGuardrail().check(None)

    assert result.allowed is False
    assert "must not be None" in result.reason


def test_non_empty_output_guardrail_allows_structured_output() -> None:
    output = {"answer": "Python uses indentation."}

    result = NonEmptyOutputGuardrail().check(output)

    assert result.allowed is True
