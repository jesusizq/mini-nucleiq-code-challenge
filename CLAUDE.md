# mini-nucleiq

Analyzes breast-tissue samples (arrays of `0`/`1`) for simplified marker patterns via pluggable
algorithms, exposed as a thin HTTP API. Coding challenge for a Senior Backend role. Full design in
@PLAN.md; the original challenge brief is in @TASK.md.

## Status

Design approved; implementation proceeds only on explicit owner approval. **Read @PLAN.md before
writing code.** All code and documentation are in **English**.

## Stack

- Python (>=3.10), Poetry, FastAPI (sync), httpx, pydantic-settings, structlog
- Tests: pytest + respx. Quality: black, ruff, mypy (strict), pre-commit, GitHub Actions CI
- Docker: multistage, `python:3.12-slim` runtime, non-root

## Architecture (hexagonal-lite: pure domain + two seams)

Dependencies point inward. The domain never imports I/O; the concrete HTTP client is injected at the
composition root (`api/app.py`).

- `src/mini_nucleiq/domain/` — `Sample`, `Algorithm` Strategy (even-zeroes, contiguous-ones,
  surrounded-ones), `registry`, `analysis`/aggregation, `errors`. No I/O.
- `src/mini_nucleiq/ports/` — `SampleRepository` Protocol.
- `src/mini_nucleiq/application/` — `AnalyzeSample` use case.
- `src/mini_nucleiq/adapters/` — `HttpSampleRepository` (Samples API, retry/backoff, structlog).
- `src/mini_nucleiq/api/` — FastAPI app (composition root), DTOs, error→status handlers.

## Critical Rules

- Final-result rule = "more than half" (`positives * 2 > n`), following the **brief text**. The brief's
  worked example is an **erratum** — see @PLAN.md. Do not code to the example.
- Samples API endpoint is `{base}/samples/{name}.json` (the brief's `View Sample` path is wrong).
- Threshold uses **integer arithmetic and strict `>`** (30% does NOT pass a `> 30%` threshold).
- Domain stays **pure**: no `fastapi`/`httpx`/`structlog` imports under `domain/`.
- Add a new algorithm = new `Algorithm` subclass + registry entry; never touch the orchestrator (OCP).
- Full type hints; `mypy --strict` must pass; no bare `Any`.
- Tests are deterministic and **network-free**: inject a fake `SampleRepository`, mock httpx with respx,
  inject `sleep` in retry. Cover edges (empty sample, exactly-at-threshold).

## Commands

`make install` · `make test` · `make lint` (ruff + mypy) · `make format` (black) · `make run` ·
`make docker-build` · `make docker-run`

## Conventions

Domain-specific conventions live in `.claude/rules/` (python, architecture).

**Git:** never squash (the brief wants progression); one logical change per commit, tests included.
**Never** add `Co-Authored-By` / "Generated with" or any AI-attribution trailer to commit messages.

## Self-Improvement Protocol

When I correct you or you discover a mistake:
1. Fix the immediate issue.
2. Decide whether it is a recurring pattern worth capturing.
3. Propose an update to the right place: CLAUDE.md (universal rules), `.claude/rules/*.md`
   (domain conventions), or PLAN.md (design changes).
4. Apply only after I confirm. Keep CLAUDE.md under 100 lines.

## Communication Style

Be direct and concise. No pleasantries, no sign-offs, no restating the question. Don't narrate what
you're about to do — just do it. Explain the WHY only when the decision is non-obvious.
