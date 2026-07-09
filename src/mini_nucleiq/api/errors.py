"""Map domain errors to HTTP status codes at the edge (the core stays HTTP-agnostic)."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from dataclasses import dataclass

import structlog
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from mini_nucleiq.domain.errors import (
    InvalidSampleDataError,
    MiniNucleiqError,
    SampleNotFoundError,
    SamplesApiError,
    UnknownAlgorithmError,
)

_log = structlog.get_logger(__name__)

_UPSTREAM_DETAIL = "upstream samples source error"
_UNEXPECTED_DETAIL = "internal error"


@dataclass(frozen=True)
class _Rule:
    status: int
    #: Client-facing message; None echoes str(exc) (safe for 4xx client mistakes, not for 5xx).
    public_detail: str | None


#: Starlette resolves the most specific registered type via MRO, so _TransientSamplesApiError
#: routes as SamplesApiError (502) and any unmapped MiniNucleiqError falls back to 500.
_RULES: dict[type[MiniNucleiqError], _Rule] = {
    UnknownAlgorithmError: _Rule(400, None),
    SampleNotFoundError: _Rule(404, None),
    SamplesApiError: _Rule(502, _UPSTREAM_DETAIL),
    InvalidSampleDataError: _Rule(502, _UPSTREAM_DETAIL),
    MiniNucleiqError: _Rule(500, _UNEXPECTED_DETAIL),
}


def _make_handler(rule: _Rule) -> Callable[[Request, Exception], Awaitable[JSONResponse]]:
    async def handler(request: Request, exc: Exception) -> JSONResponse:
        if rule.status >= 500:
            # Log the real cause server-side; never leak upstream internals to the client.
            _log.error("request_failed", status=rule.status, path=request.url.path, error=str(exc))
        detail = str(exc) if rule.public_detail is None else rule.public_detail
        return JSONResponse(status_code=rule.status, content={"detail": detail})

    return handler


def register_error_handlers(app: FastAPI) -> None:
    """Wire one handler per domain error type onto the app (base type is the fallback)."""
    for error_type, rule in _RULES.items():
        app.add_exception_handler(error_type, _make_handler(rule))
