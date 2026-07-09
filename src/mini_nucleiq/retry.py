"""A tiny, dependency-free retry helper with exponential backoff and injectable sleep."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import TypeVar

T = TypeVar("T")


@dataclass(frozen=True)
class RetryPolicy:
    """How many times to retry and how long to wait between attempts."""

    #: Retries attempted after the initial call (0 disables retrying).
    max_retries: int = 2
    #: Base delay in seconds; attempt ``k`` waits ``backoff_seconds * 2**(k-1)``.
    backoff_seconds: float = 0.2

    def backoff_for(self, retry_number: int) -> float:
        """Seconds to wait before the given 1-based retry (exponential)."""
        return self.backoff_seconds * (1 << (retry_number - 1))


def call_with_retry(
    operation: Callable[[], T],
    *,
    policy: RetryPolicy,
    retry_on: Callable[[Exception], bool],
    sleep: Callable[[float], None],
    on_retry: Callable[[Exception, int, float], None] | None = None,
) -> T:
    """Call ``operation``, retrying while ``retry_on`` accepts the raised exception."""
    attempt = 0
    while True:
        try:
            return operation()
        except Exception as exc:
            if attempt >= policy.max_retries or not retry_on(exc):
                raise
            attempt += 1
            delay = policy.backoff_for(attempt)
            if on_retry is not None:
                on_retry(exc, attempt, delay)
            sleep(delay)
