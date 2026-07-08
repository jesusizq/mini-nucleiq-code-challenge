"""Registry mapping algorithm names to instances."""

from __future__ import annotations

from collections.abc import Iterable

from mini_nucleiq.domain.algorithms import (
    Algorithm,
    ContiguousOnes,
    EvenZeroes,
    SurroundedOnes,
)
from mini_nucleiq.domain.errors import UnknownAlgorithmError


class AlgorithmRegistry:
    """Resolves algorithm names to `Algorithm` instances."""

    def __init__(self, algorithms: Iterable[Algorithm]) -> None:
        self._by_name: dict[str, Algorithm] = {}
        for algo in algorithms:
            if algo.name in self._by_name:
                raise ValueError(f"duplicate algorithm name: {algo.name!r}")
            self._by_name[algo.name] = algo

    def resolve(self, name: str) -> Algorithm:
        try:
            return self._by_name[name]
        except KeyError:
            available = ", ".join(sorted(self._by_name)) or "(none)"
            raise UnknownAlgorithmError(
                f"unknown algorithm {name!r}; available: {available}"
            ) from None

    def available(self) -> tuple[str, ...]:
        """Names of the registered algorithms, in registration order."""
        return tuple(self._by_name)


def default_registry() -> AlgorithmRegistry:
    """The registry wired with every built-in algorithm."""
    return AlgorithmRegistry([EvenZeroes(), ContiguousOnes(), SurroundedOnes()])
