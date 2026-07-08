"""Result value objects for a sample analysis."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from enum import Enum


class Verdict(str, Enum):
    """Outcome of a single algorithm or of the overall sample analysis."""

    POSITIVE = "POSITIVE"
    NEGATIVE = "NEGATIVE"


@dataclass(frozen=True, slots=True)
class AlgorithmResult:
    """Outcome of running a single algorithm over a sample.

    `positivity` is the exact percentage (positive cells over total).
    """

    algorithm: str
    positive_cells: int
    positivity: float
    result: Verdict


@dataclass(frozen=True, slots=True)
class AnalysisResult:
    """Outcome of analyzing a sample with zero or more algorithms."""

    sample_name: str
    algorithms: tuple[AlgorithmResult, ...]
    result: Verdict


def aggregate(sample_name: str, results: Sequence[AlgorithmResult]) -> AnalysisResult:
    """Combine per-algorithm results into a final verdict.

    The sample is POSITIVE if strictly more than half of the algorithms are positive
    (``positives * 2 > n``); ties and the empty case are NEGATIVE.
    """
    positives = sum(1 for result in results if result.result is Verdict.POSITIVE)
    verdict = Verdict.POSITIVE if positives * 2 > len(results) else Verdict.NEGATIVE
    return AnalysisResult(sample_name=sample_name, algorithms=tuple(results), result=verdict)
