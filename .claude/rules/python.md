---
paths:
  - '**/*.py'
---

# Python Standards

- Target Python `>=3.10`. Full type hints on all functions and public attributes.
- `mypy --strict` must pass. No bare `Any`; prefer precise types, `Protocol`, and generics.
- Format with **black** (line length 100); lint with **ruff**. Both run in pre-commit.
- Value objects: `@dataclass(frozen=True)`. Ports/interfaces: `typing.Protocol` (structural typing, DIP).
- Use SOLID principles. Extract shared logic — no duplication (DRY).
- Explicit, typed exceptions; no silent failures. Domain errors live in `domain/errors.py`.
- No I/O, logging, or global mutable state inside the domain layer.
- Tests: **pytest**, parametrized where it removes duplication; deterministic and network-free.
- Naming: `snake_case` functions/variables, `PascalCase` classes, `UPPER_SNAKE` constants.
