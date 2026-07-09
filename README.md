# mini-nucleiq

Analyze breast-tissue samples for simplified marker patterns. Given a **sample name** and **one or
more algorithms**, `mini-nucleiq` fetches the sample's cells (an array of `0`/`1`) from the external
**Samples API**, runs each algorithm (producing positive-cell counts and a positivity percentage),
and aggregates a final **POSITIVE / NEGATIVE** result. It is exposed as a thin HTTP API over a pure,
well-tested core.

The original challenge brief is preserved verbatim in [`TASK.md`](TASK.md).

## Quickstart

Requires Python `>=3.10` and [Poetry](https://python-poetry.org/).

```bash
make install          # install dependencies (+ pre-commit hooks)
make test             # run the test suite (network-free)
make run              # serve on http://localhost:8000
```

Or run it in a container:

```bash
make docker-build
make docker-run       # serve on http://localhost:8000
```

With the service running, in another terminal:

```bash
make smoke            # curl the endpoints: happy path + the 400/404/422 cases
```

## API

The service takes a sample name and one or more algorithms, fetches the sample's cells from the
Samples API, runs each algorithm, and returns the per-algorithm outcomes plus the aggregated verdict.

### `POST /v1/analyze`

```bash
curl -s -X POST http://localhost:8000/v1/analyze \
  -H 'Content-Type: application/json' \
  -d '{"sample":"sample-c","algorithms":["even-zeroes","contiguous-ones","surrounded-ones"]}'
```

```jsonc
{
  "sample": "sample-c",
  "algorithms": [
    {"algorithm": "even-zeroes",     "positive_cells": 3, "positivity": 30.0, "result": "NEGATIVE"},
    {"algorithm": "contiguous-ones", "positive_cells": 2, "positivity": 20.0, "result": "NEGATIVE"},
    {"algorithm": "surrounded-ones", "positive_cells": 2, "positivity": 20.0, "result": "POSITIVE"}
  ],
  "result": "NEGATIVE"
}
```

Interactive OpenAPI/Swagger docs are served by the running app at
[`http://localhost:8000/docs`](http://localhost:8000/docs) (a runtime endpoint, not a folder).

### `GET /health`

Unversioned liveness probe returning `{"status": "ok"}` (used by the Docker `HEALTHCHECK`).

## Algorithms

Each algorithm scans the cell array (indexes start at `0`) and counts *positive cells*; it is
positive when the positivity **strictly exceeds** its threshold.

| Algorithm         | A cell is positive when…                               | Threshold |
| ----------------- | ------------------------------------------------------ | --------- |
| `even-zeroes`     | it is a `0` at an even index                           | `> 30%`   |
| `contiguous-ones` | it is a `1` whose previous cell is also `1`            | `> 20%`   |
| `surrounded-ones` | it is a `1` whose previous and next cells are both `0` | `> 10%`   |

The **final result** is `POSITIVE` when **more than half** of the selected algorithms are positive,
otherwise `NEGATIVE`.

## Architecture

Hexagonal-lite: a **pure domain** behind a thin HTTP layer.

```
HTTP request
   │
   ▼
api/          FastAPI edge — DTO validation, error→status mapping, composition root (wiring)
   │
   ▼
application/  AnalyzeSample use case — resolve algorithms, fetch sample, analyze, aggregate
   │                        │
   ▼                        ▼
domain/ (pure)          ports/ SampleRepository (Protocol)
  Sample, Algorithm         │
  registry, analysis        ▼
                        adapters/ HttpSampleRepository ──▶ Samples API (httpx, retry/backoff)
```

- **`Algorithm` (Strategy)** — the brief asks for "one or more algorithms". Adding one is a new
  subclass + a registry entry; the use case and orchestrator never change (Open/Closed).
- **`SampleRepository` (port)** — "integrate with the Samples API" plus wanting deterministic,
  network-free tests forces a seam. A different source (S3, DB, PACS) is a new adapter; the core is
  untouched.

## Configuration

Set via environment variables (see [`.env.example`](.env.example)); every value has a sensible default
in `settings.py`.

| Variable                       | Default                                                                 | Purpose                        |
| ------------------------------ | ----------------------------------------------------------------------- | ------------------------------ |
| `SAMPLES_API_BASE_URL`         | `https://raw.githubusercontent.com/cellsia/mini-nucleiq-code-challenge/main` | Base URL of the Samples API |
| `SAMPLES_API_TIMEOUT_SECONDS`  | `5.0`                                                                    | Per-request timeout            |
| `SAMPLES_API_MAX_RETRIES`      | `2`                                                                     | Retries on transient failures  |
| `SAMPLES_API_BACKOFF_SECONDS`  | `0.2`                                                                    | Base for exponential backoff   |

Override any of them via the environment, e.g. `docker run --rm -p 8000:8000 -e
SAMPLES_API_TIMEOUT_SECONDS=10 mini-nucleiq`.

## Testing

`pytest`, deterministic and **network-free**: the use case is exercised with an in-memory fake
repository, the HTTP adapter is mocked with `respx`, and retry backoff is asserted via an injected
`sleep` (no real waiting). Run with `make test`.

## Decisions & trade-offs

- **Final-result rule follows the brief's text ("more than half"), not its example.** The brief's
  worked example prints `POSITIVE` with only 1/3 algorithms positive, which contradicts its own rule.
  We implement the rule (`positives * 2 > n`); `sample-c` is therefore **NEGATIVE**, and the example
  line is treated as an **erratum**.
- **Corrected Samples API URL.** The brief's `View Sample` path doubles the repo segment; the endpoint
  that actually responds is `{base}/samples/{name}.json`.
- **Strict `>` with integer arithmetic.** Thresholds compare `positive * 100 > threshold_pct * total`,
  so exactly-at-threshold (e.g. 30% for a `> 30%` rule) is **NEGATIVE**. `positivity` is rounded only
  for display; the verdict never uses the rounded value.
- **`contiguous-ones` interpretation.** Counts each `1` immediately preceded by another `1` (every `1`
  in a run except the first) — validated against the brief's `sample-c` numbers (2 → 20%).
- **Duplicate algorithm names are de-duplicated** (first occurrence wins) at the edge, so repeating one
  cannot double its weight in the final rule.
- **5xx responses stay generic.** Upstream failures return a generic message and log the real cause
  server-side, rather than leaking internal detail to clients.
- **Synchronous** for simplicity (`def` endpoints, `httpx.Client`); moving to async is a localized
  change behind the same port.

## Scaling to a real system

Cheap hooks are in place (versioned API, environment-based config, upstream timeout + retry/backoff,
`/health`, structured logging with `structlog`). Doors left open, documented but not built:

- **Async / queue processing** for heavy whole-slide images (submit returns a job id).
- **Alternative sample sources** — a new `SampleRepository` adapter (S3, PACS, DB); the core is untouched.
- **Throughput** — run multiple uvicorn workers (or gunicorn) behind the container.
- **API concerns** — auth, rate limiting, and metrics at the edge.

## A note on process

This project was built with AI assistance, stated openly. What the brief asks to see — how I think and
solve problems — is what the codebase encodes: the architecture, the decisions, the trade-offs, and the review of every change. I use the AI as a fast pair of hands under my direction; the judgment — what to build, what to leave out, and the bar it is held to (SOLID/DRY,
`mypy --strict`, deterministic network-free tests, commits that show the progression) — is mine. I am
happy to walk through any decision here and the reasoning behind it.
