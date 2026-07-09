"""The AnalyzeSample use case: fetch a sample, run algorithms, aggregate a verdict."""

from __future__ import annotations

from collections.abc import Sequence

from mini_nucleiq.domain.analysis import AnalysisResult, aggregate
from mini_nucleiq.domain.registry import AlgorithmRegistry
from mini_nucleiq.ports.sample_repository import SampleRepository


class AnalyzeSample:
    """Orchestrates a single analysis over the pure domain and the sample source.

    Collaborators are injected (DIP), so the use case knows nothing about HTTP or
    FastAPI: it is exercised in tests with an in-memory repository and no network.
    """

    def __init__(self, repository: SampleRepository, registry: AlgorithmRegistry) -> None:
        self._repository = repository
        self._registry = registry

    def execute(self, sample_name: str, algorithm_names: Sequence[str]) -> AnalysisResult:
        """Analyze ``sample_name`` with the named algorithms and aggregate the result."""
        algorithms = [self._registry.resolve(name) for name in algorithm_names]
        if not algorithms:
            return aggregate(sample_name, [])
        sample = self._repository.get(sample_name)
        results = [algorithm.analyze(sample) for algorithm in algorithms]
        return aggregate(sample_name, results)
