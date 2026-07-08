"""Marker-detection algorithms"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import ClassVar

from mini_nucleiq.domain.analysis import AlgorithmResult, Verdict
from mini_nucleiq.domain.sample import Sample


class Algorithm(ABC):
    """A marker-detection rule over a sample's cells."""

    name: ClassVar[str]
    #: Positivity threshold in percent; the algorithm is positive strictly above it.
    threshold_pct: ClassVar[int]

    def __init_subclass__(cls, **kwargs: object) -> None:
        # Enforce the OCP extension contract at class-definition (import) time, not deep in analyze.
        super().__init_subclass__(**kwargs)
        if not getattr(cls, "name", "") or not hasattr(cls, "threshold_pct"):
            raise TypeError(f"{cls.__name__} must define 'name' and 'threshold_pct'")

    @abstractmethod
    def count_positive(self, cells: tuple[int, ...]) -> int:
        """Return how many cells are positive under this algorithm's rule."""

    def analyze(self, sample: Sample) -> AlgorithmResult:
        total = sample.size
        positive = self.count_positive(sample.cells)
        positivity = positive * 100 / total if total else 0.0
        is_positive = positive * 100 > self.threshold_pct * total
        return AlgorithmResult(
            algorithm=self.name,
            positive_cells=positive,
            positivity=positivity,
            result=Verdict.POSITIVE if is_positive else Verdict.NEGATIVE,
        )


class EvenZeroes(Algorithm):
    """A cell is positive when it is a 0 at an even index."""

    name = "even-zeroes"
    threshold_pct = 30

    def count_positive(self, cells: tuple[int, ...]) -> int:
        return sum(1 for index, cell in enumerate(cells) if index % 2 == 0 and cell == 0)


class ContiguousOnes(Algorithm):
    """A cell is positive when it is a 1 immediately preceded by another 1."""

    name = "contiguous-ones"
    threshold_pct = 20

    def count_positive(self, cells: tuple[int, ...]) -> int:
        return sum(1 for i in range(1, len(cells)) if cells[i] == 1 and cells[i - 1] == 1)


class SurroundedOnes(Algorithm):
    """A cell is positive when it is a 1 whose previous and next cells are both 0."""

    name = "surrounded-ones"
    threshold_pct = 10

    def count_positive(self, cells: tuple[int, ...]) -> int:
        # range(1, len - 1) naturally excludes the edges, which can never be surrounded.
        return sum(
            1
            for i in range(1, len(cells) - 1)
            if cells[i] == 1 and cells[i - 1] == 0 and cells[i + 1] == 0
        )
