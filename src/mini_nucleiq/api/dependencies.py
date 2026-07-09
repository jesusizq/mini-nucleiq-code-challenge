"""FastAPI dependency wiring shared by the routes (kept separate to avoid import cycles).

The composition root writes the use case with ``set_analyze_sample`` and the routes read it
with ``get_analyze_sample``; both share a single state key so writer and reader cannot drift.
"""

from __future__ import annotations

from typing import cast

from fastapi import FastAPI, Request

from mini_nucleiq.application.analyze_sample import AnalyzeSample

_ANALYZE_SAMPLE_KEY = "analyze_sample"


def set_analyze_sample(app: FastAPI, use_case: AnalyzeSample) -> None:
    """Store the wired use case on app state (called by the composition root at startup)."""
    setattr(app.state, _ANALYZE_SAMPLE_KEY, use_case)


def get_analyze_sample(request: Request) -> AnalyzeSample:
    """Provide the use case wired at startup; tests override this to inject a fake."""
    return cast(AnalyzeSample, getattr(request.app.state, _ANALYZE_SAMPLE_KEY))
