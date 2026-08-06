from enterprise_agent_platform.orchestration.retry import RetryPolicy


def test_exponential_backoff() -> None:
    policy = RetryPolicy(
        max_attempts=5,
        base_delay_seconds=1,
        max_delay_seconds=30,
        jitter_seconds=0,
    )

    assert policy.get_delay(1) == 1
    assert policy.get_delay(2) == 2
    assert policy.get_delay(3) == 4
    assert policy.get_delay(4) == 8
    assert policy.get_delay(5) == 16


def test_exponential_backoff_respects_max_delay() -> None:
    policy = RetryPolicy(
        max_attempts=10,
        base_delay_seconds=10,
        max_delay_seconds=30,
        jitter_seconds=0,
    )

    assert policy.get_delay(1) == 10
    assert policy.get_delay(2) == 20
    assert policy.get_delay(3) == 30
    assert policy.get_delay(4) == 30
    assert policy.get_delay(5) == 30


def test_delay_includes_jitter() -> None:
    policy = RetryPolicy(
        max_attempts=5,
        base_delay_seconds=1,
        max_delay_seconds=30,
        jitter_seconds=0.5,
    )

    delay = policy.get_delay(1)

    assert 1 <= delay <= 1.5
