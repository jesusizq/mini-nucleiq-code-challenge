from __future__ import annotations

import structlog
from structlog.typing import Processor


def configure_logging(*, json_logs: bool = False) -> None:
    """Configure structlog once at startup (the composition root calls this)."""
    renderer: Processor = (
        structlog.processors.JSONRenderer() if json_logs else structlog.dev.ConsoleRenderer()
    )
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            renderer,
        ],
        cache_logger_on_first_use=True,
    )
