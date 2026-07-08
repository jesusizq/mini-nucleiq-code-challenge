import pytest

from mini_nucleiq.domain.errors import InvalidSampleDataError
from mini_nucleiq.domain.sample import Sample


def test_size_counts_cells():
    assert Sample("s", (0, 1, 1)).size == 3


def test_empty_sample_is_allowed():
    assert Sample("empty", ()).size == 0


@pytest.mark.parametrize("bad", [2, -1, 9])
def test_non_binary_cell_is_rejected(bad):
    with pytest.raises(InvalidSampleDataError):
        Sample("bad", (0, bad, 1))


@pytest.mark.parametrize("boolean", [True, False])
def test_boolean_cell_is_rejected(boolean):
    # bool is an int subclass; the domain must not silently accept upstream JSON true/false.
    with pytest.raises(InvalidSampleDataError):
        Sample("bad", (0, boolean))
