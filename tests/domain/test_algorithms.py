import pytest

from mini_nucleiq.domain.algorithms import (
    Algorithm,
    ContiguousOnes,
    EvenZeroes,
    SurroundedOnes,
)
from mini_nucleiq.domain.analysis import Verdict
from mini_nucleiq.domain.sample import Sample

# The worked example from the brief (TASK.md): 10 cells.
SAMPLE_C = (0, 0, 1, 0, 0, 1, 0, 1, 1, 1)


@pytest.mark.parametrize(
    ("algorithm", "positive", "positivity", "result"),
    [
        (EvenZeroes(), 3, 30.0, Verdict.NEGATIVE),
        (ContiguousOnes(), 2, 20.0, Verdict.NEGATIVE),
        (SurroundedOnes(), 2, 20.0, Verdict.POSITIVE),
    ],
)
def test_sample_c_matches_brief(algorithm, positive, positivity, result):
    analyzed = algorithm.analyze(Sample("sample-c", SAMPLE_C))
    assert analyzed.algorithm == algorithm.name
    assert analyzed.positive_cells == positive
    assert analyzed.positivity == pytest.approx(positivity)
    assert analyzed.result is result


@pytest.mark.parametrize("algorithm", [EvenZeroes(), ContiguousOnes(), SurroundedOnes()])
def test_empty_sample_is_negative_without_error(algorithm):
    analyzed = algorithm.analyze(Sample("empty", ()))
    assert analyzed.positive_cells == 0
    assert analyzed.positivity == 0.0
    assert analyzed.result is Verdict.NEGATIVE


def test_even_zeroes_counts_zeros_at_even_indices():
    # even indices 0,2,4 all hold 0 -> 3/5 = 60% > 30% -> POSITIVE
    analyzed = EvenZeroes().analyze(Sample("s", (0, 1, 0, 1, 0)))
    assert analyzed.positive_cells == 3
    assert analyzed.result is Verdict.POSITIVE


def test_contiguous_ones_needs_a_preceding_one():
    assert ContiguousOnes().count_positive((1, 0, 0)) == 0  # a lone leading 1 never counts
    assert ContiguousOnes().count_positive((1, 1, 1)) == 2  # a run of three yields two


def test_surrounded_ones_requires_zero_neighbours_on_both_sides():
    assert SurroundedOnes().count_positive((0, 1, 0)) == 1  # flanked by zeros -> surrounded
    assert SurroundedOnes().count_positive((1, 0, 1, 0, 1)) == 1  # only the middle 1 (index 2)
    # a 1 in the middle of a run is NOT surrounded: its neighbours are 1s, not 0s.
    assert SurroundedOnes().count_positive((1, 1, 1)) == 0
    # a 1 at either edge has no neighbour on one side, so it never counts.
    assert SurroundedOnes().count_positive((1, 0)) == 0
    assert SurroundedOnes().count_positive((0, 1)) == 0


def test_edge_length_and_uniform_samples():
    # single element: never contiguous nor surrounded; even-zeroes sees a 0 at index 0.
    assert EvenZeroes().count_positive((0,)) == 1
    assert EvenZeroes().count_positive((1,)) == 0
    assert ContiguousOnes().count_positive((1,)) == 0
    assert SurroundedOnes().count_positive((1,)) == 0

    # all ones: no even-zeroes, no surrounded; every 1 after the first is contiguous.
    assert EvenZeroes().count_positive((1, 1, 1, 1)) == 0
    assert ContiguousOnes().count_positive((1, 1, 1, 1)) == 3
    assert SurroundedOnes().count_positive((1, 1, 1, 1)) == 0

    # all zeros: even-zeroes counts indices 0 and 2; the ones-based algorithms count nothing.
    assert EvenZeroes().count_positive((0, 0, 0, 0)) == 2
    assert ContiguousOnes().count_positive((0, 0, 0, 0)) == 0
    assert SurroundedOnes().count_positive((0, 0, 0, 0)) == 0


@pytest.mark.parametrize(
    ("algorithm", "cells", "expected_positive"),
    [
        # even-zeroes at exactly 30% (3/10) must NOT pass a strict "> 30%".
        (EvenZeroes(), (0, 0, 1, 0, 0, 1, 0, 1, 1, 1), 3),
        # surrounded-ones at exactly 10% (1/10) must NOT pass a strict "> 10%".
        (SurroundedOnes(), (0, 1, 0, 0, 0, 0, 0, 0, 0, 0), 1),
    ],
)
def test_exactly_at_threshold_is_negative_by_strict_gt(algorithm, cells, expected_positive):
    analyzed = algorithm.analyze(Sample("s", cells))
    assert analyzed.positive_cells == expected_positive
    assert analyzed.result is Verdict.NEGATIVE


def test_subclass_missing_name_or_threshold_is_rejected():
    # The OCP extension contract is enforced at class-definition time, not at analyze() time.
    with pytest.raises(TypeError):

        class _Incomplete(Algorithm):  # forgets name / threshold_pct
            def count_positive(self, cells: tuple[int, ...]) -> int:
                return 0
