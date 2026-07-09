import httpx
import pytest
import respx

from mini_nucleiq.adapters.http_sample_repository import HttpSampleRepository
from mini_nucleiq.domain.errors import (
    InvalidSampleDataError,
    SampleNotFoundError,
    SamplesApiError,
)
from mini_nucleiq.domain.sample import Sample
from mini_nucleiq.retry import RetryPolicy

BASE_URL = "https://samples.test"
SAMPLE_C_URL = f"{BASE_URL}/samples/sample-c.json"
SAMPLE_C_BODY = {"name": "sample-c", "cells": [0, 0, 1, 0, 0, 1, 0, 1, 1, 1]}


def _repo(
    client: httpx.Client, *, max_retries: int = 2
) -> tuple[HttpSampleRepository, list[float]]:
    """Build a repository whose injected sleep only records the delays it is asked to wait."""
    delays: list[float] = []
    repo = HttpSampleRepository(
        client,
        base_url=BASE_URL,
        retry_policy=RetryPolicy(max_retries=max_retries, backoff_seconds=1.0),
        sleep=delays.append,
    )
    return repo, delays


@respx.mock
def test_fetches_and_parses_sample_from_correct_url() -> None:
    route = respx.get(SAMPLE_C_URL).mock(return_value=httpx.Response(200, json=SAMPLE_C_BODY))

    with httpx.Client() as client:
        repo, delays = _repo(client)
        sample = repo.get("sample-c")

    assert sample == Sample("sample-c", (0, 0, 1, 0, 0, 1, 0, 1, 1, 1))
    assert route.call_count == 1
    assert str(route.calls[0].request.url) == SAMPLE_C_URL
    assert delays == []  # a clean fetch never sleeps


@respx.mock
def test_404_maps_to_sample_not_found_without_retry() -> None:
    route = respx.get(SAMPLE_C_URL).mock(return_value=httpx.Response(404))

    with httpx.Client() as client:
        repo, delays = _repo(client)
        with pytest.raises(SampleNotFoundError):
            repo.get("sample-c")

    assert route.call_count == 1  # a missing sample is deterministic; do not retry
    assert delays == []


@respx.mock
def test_server_error_is_retried_then_raises_api_error() -> None:
    route = respx.get(SAMPLE_C_URL).mock(return_value=httpx.Response(503))

    with httpx.Client() as client:
        repo, delays = _repo(client, max_retries=2)
        with pytest.raises(SamplesApiError):
            repo.get("sample-c")

    assert route.call_count == 3  # initial call + 2 retries
    assert delays == [1.0, 2.0]  # exponential backoff


@respx.mock
def test_recovers_after_a_transient_server_error() -> None:
    route = respx.get(SAMPLE_C_URL).mock(
        side_effect=[httpx.Response(503), httpx.Response(200, json=SAMPLE_C_BODY)]
    )

    with httpx.Client() as client:
        repo, delays = _repo(client)
        sample = repo.get("sample-c")

    assert sample.size == 10
    assert route.call_count == 2
    assert delays == [1.0]


@respx.mock
def test_network_error_maps_to_api_error_and_is_retried() -> None:
    route = respx.get(SAMPLE_C_URL).mock(side_effect=httpx.ConnectError("boom"))

    with httpx.Client() as client:
        repo, delays = _repo(client, max_retries=1)
        with pytest.raises(SamplesApiError):
            repo.get("sample-c")

    assert route.call_count == 2  # initial call + 1 retry
    assert delays == [1.0]


@respx.mock
def test_read_timeout_maps_to_api_error_and_is_retried() -> None:
    route = respx.get(SAMPLE_C_URL).mock(side_effect=httpx.ReadTimeout("timed out"))

    with httpx.Client() as client:
        repo, delays = _repo(client, max_retries=2)
        with pytest.raises(SamplesApiError):
            repo.get("sample-c")

    assert route.call_count == 3  # timeouts are transient -> retried
    assert delays == [1.0, 2.0]


@respx.mock
def test_rate_limited_response_is_retried() -> None:
    route = respx.get(SAMPLE_C_URL).mock(return_value=httpx.Response(429))

    with httpx.Client() as client:
        repo, delays = _repo(client, max_retries=2)
        with pytest.raises(SamplesApiError):
            repo.get("sample-c")

    assert route.call_count == 3  # 429 is transient -> retried
    assert delays == [1.0, 2.0]


@respx.mock
def test_client_error_maps_to_api_error_without_retry() -> None:
    route = respx.get(SAMPLE_C_URL).mock(return_value=httpx.Response(403))

    with httpx.Client() as client:
        repo, delays = _repo(client, max_retries=2)
        with pytest.raises(SamplesApiError):
            repo.get("sample-c")

    assert route.call_count == 1  # a 4xx is deterministic -> do not retry
    assert delays == []


@respx.mock
def test_malformed_json_maps_to_invalid_data_without_retry() -> None:
    route = respx.get(SAMPLE_C_URL).mock(return_value=httpx.Response(200, content=b"not json"))

    with httpx.Client() as client:
        repo, delays = _repo(client)
        with pytest.raises(InvalidSampleDataError):
            repo.get("sample-c")

    assert route.call_count == 1  # deterministic parse failure; do not retry
    assert delays == []


@respx.mock
def test_missing_cells_field_maps_to_invalid_data() -> None:
    respx.get(SAMPLE_C_URL).mock(return_value=httpx.Response(200, json={"name": "sample-c"}))

    with httpx.Client() as client:
        repo, _ = _repo(client)
        with pytest.raises(InvalidSampleDataError):
            repo.get("sample-c")


@respx.mock
def test_non_binary_cell_maps_to_invalid_data() -> None:
    respx.get(SAMPLE_C_URL).mock(
        return_value=httpx.Response(200, json={"name": "sample-c", "cells": [0, 2, 1]})
    )

    with httpx.Client() as client:
        repo, _ = _repo(client)
        with pytest.raises(InvalidSampleDataError):
            repo.get("sample-c")
