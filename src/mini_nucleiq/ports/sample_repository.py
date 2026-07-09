"""The port through which the core obtains samples, agnostic of the concrete source."""

from __future__ import annotations

from typing import Protocol

from mini_nucleiq.domain.sample import Sample


class SampleRepository(Protocol):
    """A source of samples by name (DIP seam; adapters implement it structurally)."""

    def get(self, name: str) -> Sample:
        """Return the sample stored under ``name``.

        Raises:
            SampleNotFoundError: if the source holds no sample with that name.

        """
        ...
