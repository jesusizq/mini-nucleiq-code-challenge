"""Live integration against the real Samples API. Deselected by default; run with `-m live`."""

import httpx
import pytest

from mini_nucleiq.adapters.http_sample_repository import HttpSampleRepository
from mini_nucleiq.domain.sample import Sample
from mini_nucleiq.settings import Settings

pytestmark = pytest.mark.live


def test_fetches_sample_c_from_the_real_samples_api():
    settings = Settings()
    with httpx.Client(timeout=settings.samples_api_timeout_seconds) as client:
        repository = HttpSampleRepository(client, base_url=settings.samples_api_base_url)
        sample = repository.get("sample-c")

    assert sample == Sample("sample-c", (0, 0, 1, 0, 0, 1, 0, 1, 1, 1))
