"""Result value objects for a sample analysis."""

from __future__ import annotations

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
