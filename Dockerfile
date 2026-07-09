# syntax=docker/dockerfile:1

########################################################
# Builder - install deps, then build+install the package
########################################################
FROM python:3.12-slim AS builder

ENV PIP_NO_CACHE_DIR=1 \
    POETRY_VERSION=1.8.5 \
    POETRY_VIRTUALENVS_IN_PROJECT=true \
    POETRY_NO_INTERACTION=1

RUN pip install "poetry==${POETRY_VERSION}"

WORKDIR /app
# Dependencies first: this layer is cache-stable and only rebuilds when the lock changes.
COPY pyproject.toml poetry.lock README.md ./
RUN poetry install --only main --no-root
# Then the source: build a wheel and install it (non-editable, so the runtime needs no src copy
# and no PYTHONPATH tricks — the package lives in site-packages like any other dependency).
COPY src ./src
RUN poetry build -f wheel && /app/.venv/bin/pip install --no-deps dist/*.whl

########################################################
# Runtime - slim, non-root, no build tools
########################################################
FROM python:3.12-slim AS runtime

ENV PATH="/app/.venv/bin:${PATH}" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

RUN groupadd --system app \
    && useradd --system --gid app --home-dir /app --shell /usr/sbin/nologin app

WORKDIR /app
COPY --from=builder --chown=app:app /app/.venv /app/.venv

USER app
EXPOSE 8000

# python (already in the image) instead of curl to avoid an extra package in the slim runtime;
# stderr is dropped so a failed probe records "unhealthy" without a traceback in the health log.
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD python -c "import sys, urllib.request; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=2).status == 200 else 1)" 2>/dev/null

CMD ["uvicorn", "mini_nucleiq.api.app:app", "--host", "0.0.0.0", "--port", "8000"]
