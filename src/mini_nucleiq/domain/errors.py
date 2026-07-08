"""Domain errors. Pure (no I/O); the adapter and API layers translate them at the edges."""

from __future__ import annotations


class MiniNucleiqError(Exception):
    """Base class for all mini-nucleiq domain errors."""


class InvalidSampleDataError(MiniNucleiqError):
    """A sample's cell data is missing, malformed, or not a sequence of 0/1 values."""


class UnknownAlgorithmError(MiniNucleiqError):
    """A requested algorithm name is not registered."""
