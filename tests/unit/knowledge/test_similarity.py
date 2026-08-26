import pytest

from enterprise_agent_platform.knowledge.similarity import (
    cosine_similarity,
)


def test_same_direction() -> None:
    assert cosine_similarity(
        [1.0, 1.0],
        [2.0, 2.0],
    ) == pytest.approx(1.0)


def test_opposite_direction() -> None:
    assert cosine_similarity(
        [1.0, 1.0],
        [-1.0, -1.0],
    ) == pytest.approx(-1.0)


def test_perpendicular_direction() -> None:
    assert cosine_similarity(
        [1.0, 0.0],
        [0.0, 1.0],
    ) == pytest.approx(0.0)


def test_diagonal_direction() -> None:
    assert round(
        cosine_similarity(
            [1.0, 1.0],
            [1.0, 0.0],
        ),
        4,
    ) == pytest.approx(0.7071)
