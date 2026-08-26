import math


def cosine_similarity(
    left: list[float],
    right: list[float],
) -> float:
    """Return the cosine similarity between two vectors."""

    dot = dot_product(left, right)
    left_norm = magnitude(left)
    right_norm = magnitude(right)

    if left_norm == 0 or right_norm == 0:
        raise ValueError("Cannot compute cosine similarity for zero-magnitude vector.")

    return dot / (left_norm * right_norm)


def dot_product(
    left: list[float],
    right: list[float],
) -> float:
    return sum(x * y for x, y in zip(left, right, strict=True))


def magnitude(
    vector: list[float],
) -> float:
    return math.sqrt(sum(value * value for value in vector))
