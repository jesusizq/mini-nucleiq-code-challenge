import pytest

from mini_nucleiq.domain.analysis import AlgorithmResult, Verdict, aggregate

P = Verdict.POSITIVE
N = Verdict.NEGATIVE


def _result(verdict: Verdict) -> AlgorithmResult:
    return AlgorithmResult(algorithm="x", positive_cells=0, positivity=0.0, result=verdict)


@pytest.mark.parametrize(
    ("verdicts", "expected"),
    [
        ([], N),  # empty -> NEGATIVE, no error
        ([P], P),
        ([N], N),
        ([P, N], N),  # tie 1/2 is not "more than half"
        ([P, P], P),
        ([P, N, N], N),  # the brief's example: 1/3 positive -> NEGATIVE
        ([P, P, N], P),  # 2/3 -> POSITIVE
        ([P, P, N, N], N),  # tie 2/4 -> NEGATIVE
        ([P, P, P, N], P),  # 3/4 -> POSITIVE
    ],
)
def test_more_than_half_rule(verdicts, expected):
    results = [_result(v) for v in verdicts]
    analysis = aggregate("sample-x", results)
    assert analysis.result is expected
    assert analysis.sample_name == "sample-x"
    assert analysis.algorithms == tuple(results)  # order and objects preserved
