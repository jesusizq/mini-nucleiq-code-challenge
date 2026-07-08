import pytest

from mini_nucleiq.domain.algorithms import EvenZeroes
from mini_nucleiq.domain.errors import UnknownAlgorithmError
from mini_nucleiq.domain.registry import AlgorithmRegistry, default_registry


def test_resolves_known_algorithm():
    algorithm = default_registry().resolve("even-zeroes")
    assert isinstance(algorithm, EvenZeroes)
    assert algorithm.name == "even-zeroes"


def test_unknown_algorithm_raises():
    with pytest.raises(UnknownAlgorithmError):
        default_registry().resolve("does-not-exist")


def test_available_lists_registered_names():
    assert AlgorithmRegistry([EvenZeroes()]).available() == ("even-zeroes",)


def test_default_registry_exposes_the_three_algorithms():
    assert set(default_registry().available()) == {
        "even-zeroes",
        "contiguous-ones",
        "surrounded-ones",
    }


def test_duplicate_algorithm_name_is_rejected():
    with pytest.raises(ValueError):
        AlgorithmRegistry([EvenZeroes(), EvenZeroes()])
