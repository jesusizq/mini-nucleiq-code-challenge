"""The Sample value object: an immutable tissue sample."""

from __future__ import annotations

from dataclasses import dataclass

from mini_nucleiq.domain.errors import InvalidSampleDataError


@dataclass(frozen=True, slots=True)
class Sample:
    """A tissue sample identified by name, holding its cells (each 0 or 1)."""

    name: str
    cells: tuple[int, ...]

    def __post_init__(self) -> None:
        for cell in self.cells:
            if type(cell) is not int or cell not in (0, 1):
                raise InvalidSampleDataError(
                    f"sample {self.name!r} has a non-binary cell value: {cell!r}"
                )

    @property
    def size(self) -> int:
        """Total number of cells."""
        return len(self.cells)
