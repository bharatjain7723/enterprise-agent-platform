import pytest

from enterprise_agent_platform.guardrails.input import (
    MaxInputLengthGuardrail,
    NonEmptyInputGuardrail,
)


def test_non_empty_input_guardrail_allows_normal_input() -> None:
    result = NonEmptyInputGuardrail().check("Explain Python decorators.")

    assert result.allowed is True
    assert result.guardrail_name == "non_empty_input"


@pytest.mark.parametrize("user_input", ["", " ", "\n", "\t  \n"])
def test_non_empty_input_guardrail_rejects_blank_input(
    user_input: str,
) -> None:
    result = NonEmptyInputGuardrail().check(user_input)

    assert result.allowed is False
    assert "must not be empty" in result.reason


def test_max_input_length_guardrail_allows_input_at_limit() -> None:
    guardrail = MaxInputLengthGuardrail(max_length=5)

    result = guardrail.check("12345")

    assert result.allowed is True


def test_max_input_length_guardrail_rejects_input_over_limit() -> None:
    guardrail = MaxInputLengthGuardrail(max_length=5)

    result = guardrail.check("123456")

    assert result.allowed is False
    assert result.guardrail_name == "max_input_length"
    assert "exceeds the maximum of 5" in result.reason


@pytest.mark.parametrize("max_length", [0, -1])
def test_max_input_length_guardrail_rejects_invalid_configuration(
    max_length: int,
) -> None:
    with pytest.raises(ValueError, match="at least 1"):
        MaxInputLengthGuardrail(max_length=max_length)
