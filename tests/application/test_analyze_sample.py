import pytest

from mini_nucleiq.application.analyze_sample import AnalyzeSample
from mini_nucleiq.domain.analysis import Verdict
from mini_nucleiq.domain.errors import SampleNotFoundError, UnknownAlgorithmError
from mini_nucleiq.domain.registry import default_registry
from mini_nucleiq.domain.sample import Sample
from mini_nucleiq.ports.sample_repository import SampleRepository

SAMPLE_C = Sample("sample-c", (0, 0, 1, 0, 0, 1, 0, 1, 1, 1))


class FakeSampleRepository:
    """In-memory SampleRepository double; records whether the source was queried."""

    def __init__(self, *samples: Sample) -> None:
        self._by_name = {sample.name: sample for sample in samples}
        self.get_calls = 0

    def get(self, name: str) -> Sample:
        self.get_calls += 1
        try:
            return self._by_name[name]
        except KeyError:
            raise SampleNotFoundError(name) from None


def _use_case(*samples: Sample) -> tuple[AnalyzeSample, FakeSampleRepository]:
    repo = FakeSampleRepository(*samples)
    # The fake structurally satisfies the port; mypy checks the seam here.
    port: SampleRepository = repo
    return AnalyzeSample(port, default_registry()), repo


def test_full_sample_c_analysis():
    use_case, _ = _use_case(SAMPLE_C)

    analysis = use_case.execute("sample-c", ["even-zeroes", "contiguous-ones", "surrounded-ones"])

    assert analysis.sample_name == "sample-c"
    assert [
        (r.algorithm, r.positive_cells, r.positivity, r.result) for r in analysis.algorithms
    ] == [
        ("even-zeroes", 3, 30.0, Verdict.NEGATIVE),
        ("contiguous-ones", 2, 20.0, Verdict.NEGATIVE),
        ("surrounded-ones", 2, 20.0, Verdict.POSITIVE),
    ]
    # 1/3 positive -> NEGATIVE (the brief's example prints POSITIVE; treated as an erratum).
    assert analysis.result is Verdict.NEGATIVE


def test_preserves_requested_algorithm_order_and_subset():
    use_case, _ = _use_case(SAMPLE_C)

    analysis = use_case.execute("sample-c", ["surrounded-ones", "even-zeroes"])

    assert [r.algorithm for r in analysis.algorithms] == ["surrounded-ones", "even-zeroes"]
    # 1/2 positive is not "more than half".
    assert analysis.result is Verdict.NEGATIVE


def test_unknown_algorithm_propagates_without_fetching():
    use_case, repo = _use_case(SAMPLE_C)

    with pytest.raises(UnknownAlgorithmError):
        use_case.execute("sample-c", ["even-zeroes", "does-not-exist"])

    # Resolution happens before the fetch, so a bad request never hits the source.
    assert repo.get_calls == 0


def test_missing_sample_propagates():
    use_case, _ = _use_case(SAMPLE_C)

    with pytest.raises(SampleNotFoundError):
        use_case.execute("no-such-sample", ["even-zeroes"])


def test_no_algorithms_yields_negative_without_fetching():
    use_case, repo = _use_case(SAMPLE_C)

    analysis = use_case.execute("sample-c", [])

    assert analysis.algorithms == ()
    assert analysis.result is Verdict.NEGATIVE
    assert repo.get_calls == 0
