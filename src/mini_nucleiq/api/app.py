"""FastAPI app and composition root: the one place that wires concrete adapters."""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import httpx
from fastapi import FastAPI

from mini_nucleiq.adapters.http_sample_repository import HttpSampleRepository
from mini_nucleiq.api.dependencies import set_analyze_sample
from mini_nucleiq.api.errors import register_error_handlers
from mini_nucleiq.api.routes import analyze, health
from mini_nucleiq.application.analyze_sample import AnalyzeSample
from mini_nucleiq.domain.registry import default_registry
from mini_nucleiq.logging_config import configure_logging
from mini_nucleiq.retry import RetryPolicy
from mini_nucleiq.settings import Settings


def create_app(settings: Settings | None = None) -> FastAPI:
    """Build the app, wiring settings -> HTTP client -> repository -> use case."""
    resolved = settings or Settings()

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        configure_logging()
        client = httpx.Client(timeout=resolved.samples_api_timeout_seconds)
        repository = HttpSampleRepository(
            client,
            base_url=resolved.samples_api_base_url,
            retry_policy=RetryPolicy(
                max_retries=resolved.samples_api_max_retries,
                backoff_seconds=resolved.samples_api_backoff_seconds,
            ),
        )
        set_analyze_sample(app, AnalyzeSample(repository, default_registry()))
        try:
            yield
        finally:
            client.close()

    app = FastAPI(title="mini-nucleiq", version="0.1.0", lifespan=lifespan)
    register_error_handlers(app)
    app.include_router(health.router)
    app.include_router(analyze.router)
    return app


app = create_app()
