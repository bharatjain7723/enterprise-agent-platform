from agents import function_tool


@function_tool
def add(
    a: int,
    b: int,
) -> int:
    """
    Add or sum two integers together.

    Only use this tool when the user explicitly requests
    addition or summing two numbers.

    Do not use this tool for subtraction,
    multiplication,
    division,
    percentages,
    or other mathematical operations.
    """
    return a + b
