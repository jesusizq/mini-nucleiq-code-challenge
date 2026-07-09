"""HttpSampleRepository: a SampleRepository backed by the external Samples API."""

from __future__ import annotations

import time
from collections.abc import Callable

import httpx
import structlog
from structlog.typing import FilteringBoundLogger

from mini_nucleiq.domain.errors import (
    InvalidSampleDataError,
    SampleNotFoundError,
    SamplesApiError,
)
from mini_nucleiq.domain.sample import Sample
from mini_nucleiq.retry import RetryPolicy, call_with_retry


class _TransientSamplesApiError(SamplesApiError):
    """A samples-source failure worth retrying (network, timeout, 5xx, or 429).

    Still a SamplesApiError, so callers and the API layer treat it as a 502; the
    distinction only tells the retry policy which failures are worth repeating.
    """


class HttpSampleRepository:
    """A SampleRepository backed by ``{base_url}/samples/{name}.json``.

    This adapter is the seam where HTTP stays: transport and status failures are
    translated into domain errors (see ``_request``/``_parse``), and only
    transient ones are retried with backoff via an injected ``sleep``.
    """

    def __init__(
        self,
        client: httpx.Client,
        *,
        base_url: str,
        retry_policy: RetryPolicy | None = None,
        sleep: Callable[[float], None] = time.sleep,
        logger: FilteringBoundLogger | None = None,
    ) -> None:
        self._client = client
        self._base_url = base_url.rstrip("/")
        self._retry_policy = retry_policy or RetryPolicy()
        self._sleep = sleep
        self._log: FilteringBoundLogger = logger or structlog.get_logger(__name__)

    def get(self, name: str) -> Sample:
        url = f"{self._base_url}/samples/{name}.json"
        log = self._log.bind(sample=name, url=url)

        def _on_retry(exc: Exception, attempt: int, delay: float) -> None:
            log.warning("samples_api_retry", attempt=attempt, delay=delay, error=str(exc))

        response = call_with_retry(
            lambda: self._request(name, url),
            policy=self._retry_policy,
            retry_on=lambda exc: isinstance(exc, _TransientSamplesApiError),
            sleep=self._sleep,
            on_retry=_on_retry,
        )
        sample = self._parse(name, response)
        log.info("sample_fetched", cell_count=sample.size)
        return sample

    def _request(self, name: str, url: str) -> httpx.Response:
        """Perform the GET and map transport/status failures to domain errors."""
        try:
            response = self._client.get(url)
        except httpx.RequestError as exc:  # connection errors, timeouts, DNS, ...
            raise _TransientSamplesApiError(f"request to samples API failed: {exc}") from exc
        status = response.status_code
        if status == httpx.codes.OK:
            return response
        if status == httpx.codes.NOT_FOUND:
            raise SampleNotFoundError(f"sample {name!r} not found")
        if status == httpx.codes.TOO_MANY_REQUESTS or status >= httpx.codes.INTERNAL_SERVER_ERROR:
            raise _TransientSamplesApiError(f"samples API returned status {status}")
        raise SamplesApiError(f"samples API returned status {status}")

    def _parse(self, name: str, response: httpx.Response) -> Sample:
        """Turn the JSON body into a validated Sample."""
        try:
            payload = response.json()
        except ValueError as exc:  # includes json.JSONDecodeError
            raise InvalidSampleDataError(
                f"sample {name!r}: response body is not valid JSON"
            ) from exc
        if not isinstance(payload, dict) or "cells" not in payload:
            raise InvalidSampleDataError(f"sample {name!r}: response is missing a 'cells' field")
        cells = payload["cells"]
        if not isinstance(cells, list):
            raise InvalidSampleDataError(f"sample {name!r}: 'cells' is not a list")
        # Sample.__post_init__ enforces the 0/1 contract (and rejects booleans).
        return Sample(name=name, cells=tuple(cells))
