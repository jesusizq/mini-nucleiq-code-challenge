---
paths:
  - 'src/**/*.py'
  - 'tests/**/*.py'
---

# Architecture & Layering

- Hexagonal-lite. Layers: `domain` (pure) ← `application` (use cases) ← `adapters` / `api` (I/O).
  Dependencies point **inward** only.
- `domain/` MUST NOT import `fastapi`, `httpx`, `structlog`, or anything performing I/O.
- Ports are `Protocol`s in `ports/`; adapters implement them. Wiring happens only in `api/app.py`
  (the composition root) — it is the only place that constructs concrete adapters.
- New algorithm: subclass `Algorithm` and register it in `registry.py`. Do NOT edit the use case or
  the orchestrator (Open/Closed).
- New sample source: add a new `SampleRepository` adapter; the core stays untouched.
- Samples API HTTP failures map to domain errors in the adapter; the API layer maps domain errors to
  HTTP status codes (unknown algorithm → 400, missing sample → 404, empty list → 422, upstream → 502).
- Threshold comparisons: integer arithmetic and strict `>`. Aggregation: `positives * 2 > n`.
- Keep retry/backoff behind `retry.py` with an injectable `sleep` so tests never wait for real time.
