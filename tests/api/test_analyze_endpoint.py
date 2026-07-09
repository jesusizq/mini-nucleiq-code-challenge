import httpx
import respx
from fastapi.testclient import TestClient

from mini_nucleiq.api.app import create_app
from mini_nucleiq.api.dependencies import get_analyze_sample
from mini_nucleiq.application.analyze_sample import AnalyzeSample
from mini_nucleiq.domain.errors import (
    InvalidSampleDataError,
    SampleNotFoundError,
    SamplesApiError,
)
from mini_nucleiq.domain.registry import default_registry
from mini_nucleiq.domain.sample import Sample

SAMPLE_C = Sample("sample-c", (0, 0, 1, 0, 0, 1, 0, 1, 1, 1))
REMOTE_BASE = "https://samples.test"


class StubRepository:
    """A SampleRepository that returns a canned sample or raises a canned error."""

    def __init__(self, *, sample: Sample | None = None, error: Exception | None = None) -> None:
        self._sample = sample
        self._error = error

    def get(self, name: str) -> Sample:
        if self._error is not None:
            raise self._error
        assert self._sample is not None
        return self._sample


def _client(repo: StubRepository) -> TestClient:
    app = create_app()
    use_case = AnalyzeSample(repo, default_registry())
    app.dependency_overrides[get_analyze_sample] = lambda: use_case
    return TestClient(app)


# --- Edge behaviour, isolated from the network via a dependency override --------------------


def test_health_returns_ok():
    response = TestClient(create_app()).get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_analyze_returns_full_result_for_sample_c():
    client = _client(StubRepository(sample=SAMPLE_C))

    response = client.post(
        "/v1/analyze",
        json={
            "sample": "sample-c",
            "algorithms": ["even-zeroes", "contiguous-ones", "surrounded-ones"],
        },
    )

    assert response.status_code == 200
    assert response.json() == {
        "sample": "sample-c",
        "algorithms": [
            {
                "algorithm": "even-zeroes",
                "positive_cells": 3,
                "positivity": 30.0,
                "result": "NEGATIVE",
            },
            {
                "algorithm": "contiguous-ones",
                "positive_cells": 2,
                "positivity": 20.0,
                "result": "NEGATIVE",
            },
            {
                "algorithm": "surrounded-ones",
                "positive_cells": 2,
                "positivity": 20.0,
                "result": "POSITIVE",
            },
        ],
        # 1/3 positive -> NEGATIVE (the brief's POSITIVE line is an erratum).
        "result": "NEGATIVE",
    }


def test_positivity_is_rounded_for_display():
    # even-zeroes on (0, 1, 1): a single 0 at an even index -> 1 of 3 -> 33.33%.
    client = _client(StubRepository(sample=Sample("s", (0, 1, 1))))

    response = client.post("/v1/analyze", json={"sample": "s", "algorithms": ["even-zeroes"]})

    assert response.status_code == 200
    assert response.json()["algorithms"][0]["positivity"] == 33.33


def test_unknown_algorithm_returns_400():
    client = _client(StubRepository(sample=SAMPLE_C))

    response = client.post("/v1/analyze", json={"sample": "sample-c", "algorithms": ["nope"]})

    assert response.status_code == 400


def test_missing_sample_returns_404_and_echoes_detail():
    client = _client(StubRepository(error=SampleNotFoundError("sample 'x' not found")))

    response = client.post("/v1/analyze", json={"sample": "x", "algorithms": ["even-zeroes"]})

    assert response.status_code == 404
    assert response.json() == {"detail": "sample 'x' not found"}  # 4xx detail is safe to echo


def test_empty_algorithm_list_returns_422():
    client = _client(StubRepository(sample=SAMPLE_C))

    response = client.post("/v1/analyze", json={"sample": "sample-c", "algorithms": []})

    assert response.status_code == 422


def test_blank_sample_name_returns_422():
    client = _client(StubRepository(sample=SAMPLE_C))

    response = client.post("/v1/analyze", json={"sample": "", "algorithms": ["even-zeroes"]})

    assert response.status_code == 422


def test_upstream_failure_returns_502_without_leaking_detail():
    client = _client(StubRepository(error=SamplesApiError("samples API returned status 503")))

    response = client.post(
        "/v1/analyze", json={"sample": "sample-c", "algorithms": ["even-zeroes"]}
    )

    assert response.status_code == 502
    assert response.json() == {"detail": "upstream samples source error"}  # internal cause hidden


def test_malformed_upstream_data_returns_502():
    client = _client(
        StubRepository(error=InvalidSampleDataError("sample 's': 'cells' is not a list"))
    )

    response = client.post("/v1/analyze", json={"sample": "s", "algorithms": ["even-zeroes"]})

    assert response.status_code == 502
    assert response.json() == {"detail": "upstream samples source error"}


def test_duplicate_algorithms_are_deduplicated_preserving_order():
    client = _client(StubRepository(sample=SAMPLE_C))

    response = client.post(
        "/v1/analyze",
        json={
            "sample": "sample-c",
            "algorithms": ["surrounded-ones", "even-zeroes", "surrounded-ones"],
        },
    )

    assert response.status_code == 200
    assert [item["algorithm"] for item in response.json()["algorithms"]] == [
        "surrounded-ones",
        "even-zeroes",
    ]


# --- The real composition root, driven end-to-end with the lifespan (respx, still no network) -


@respx.mock
def test_real_wiring_returns_analysis(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("SAMPLES_API_BASE_URL", REMOTE_BASE)
    monkeypatch.setenv("SAMPLES_API_MAX_RETRIES", "0")
    respx.get(f"{REMOTE_BASE}/samples/sample-c.json").mock(
        return_value=httpx.Response(200, json={"name": "sample-c", "cells": list(SAMPLE_C.cells)})
    )

    with TestClient(create_app()) as client:
        response = client.post(
            "/v1/analyze", json={"sample": "sample-c", "algorithms": ["surrounded-ones"]}
        )

    assert response.status_code == 200
    assert response.json()["algorithms"] == [
        {
            "algorithm": "surrounded-ones",
            "positive_cells": 2,
            "positivity": 20.0,
            "result": "POSITIVE",
        }
    ]


@respx.mock
def test_real_wiring_maps_upstream_5xx_to_502(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("SAMPLES_API_BASE_URL", REMOTE_BASE)
    monkeypatch.setenv("SAMPLES_API_MAX_RETRIES", "0")
    respx.get(f"{REMOTE_BASE}/samples/sample-c.json").mock(return_value=httpx.Response(503))

    with TestClient(create_app()) as client:
        response = client.post(
            "/v1/analyze", json={"sample": "sample-c", "algorithms": ["even-zeroes"]}
        )

    # Exercises the real adapter -> _TransientSamplesApiError -> SamplesApiError handler (502).
    assert response.status_code == 502
    assert response.json() == {"detail": "upstream samples source error"}
