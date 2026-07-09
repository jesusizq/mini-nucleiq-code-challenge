import pytest

from mini_nucleiq.retry import RetryPolicy, call_with_retry


def test_backoff_is_exponential():
    policy = RetryPolicy(max_retries=3, backoff_seconds=0.5)
    assert [policy.backoff_for(k) for k in (1, 2, 3)] == [0.5, 1.0, 2.0]


def test_returns_first_success_without_sleeping():
    delays: list[float] = []
    calls: list[int] = []

    def operation() -> str:
        calls.append(1)
        return "ok"

    result = call_with_retry(
        operation, policy=RetryPolicy(), retry_on=lambda _: True, sleep=delays.append
    )

    assert result == "ok"
    assert len(calls) == 1
    assert delays == []


def test_retries_retryable_error_then_succeeds():
    delays: list[float] = []
    attempts: list[int] = []

    def operation() -> str:
        attempts.append(1)
        if len(attempts) < 3:
            raise ValueError("transient")
        return "ok"

    result = call_with_retry(
        operation,
        policy=RetryPolicy(max_retries=5, backoff_seconds=1.0),
        retry_on=lambda exc: isinstance(exc, ValueError),
        sleep=delays.append,
    )

    assert result == "ok"
    assert len(attempts) == 3
    assert delays == [1.0, 2.0]


def test_non_retryable_error_propagates_immediately():
    delays: list[float] = []

    def operation() -> str:
        raise KeyError("nope")

    with pytest.raises(KeyError):
        call_with_retry(
            operation,
            policy=RetryPolicy(max_retries=3),
            retry_on=lambda exc: isinstance(exc, ValueError),
            sleep=delays.append,
        )

    assert delays == []


def test_exhausts_retries_then_reraises():
    delays: list[float] = []

    def operation() -> str:
        raise ValueError("always")

    with pytest.raises(ValueError):
        call_with_retry(
            operation,
            policy=RetryPolicy(max_retries=2, backoff_seconds=1.0),
            retry_on=lambda _: True,
            sleep=delays.append,
        )

    assert delays == [1.0, 2.0]
