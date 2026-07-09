#!/usr/bin/env python3
"""Manually exercise the mini-nucleiq API once the service is up (`make run` / `make docker-run`).

Shows the happy path plus the documented error cases, so a reviewer can eyeball the behaviour
end to end without reading the tests. Standard library only — nothing to install.

Usage:
    python3 scripts/smoke.py                 # http://localhost:8000, sample-c
    python3 scripts/smoke.py sample-a        # analyze a different sample
    BASE_URL=http://localhost:9000 python3 scripts/smoke.py

Note: /v1/analyze fetches cells from the upstream Samples API, so it needs network access.
"""

from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.request

BASE_URL = os.environ.get("BASE_URL", "http://localhost:8000")
SAMPLE = sys.argv[1] if len(sys.argv) > 1 else "sample-c"
ALGORITHMS = ["even-zeroes", "contiguous-ones", "surrounded-ones"]


def call(method: str, path: str, body: dict | None = None) -> None:
    """Send a request and print the method, HTTP status, and the (pretty) JSON body."""
    data = json.dumps(body).encode() if body is not None else None
    request = urllib.request.Request(BASE_URL + path, data=data, method=method)
    if data is not None:
        request.add_header("Content-Type", "application/json")

    summary = f"{method} {path}"
    if body is not None:
        summary += f"  {json.dumps(body)}"
    print(f"→ {summary}")

    try:
        with urllib.request.urlopen(request, timeout=10) as response:
            status, payload = response.status, response.read()
    except urllib.error.HTTPError as error:  # 4xx/5xx still carry a JSON body
        status, payload = error.code, error.read()
    except urllib.error.URLError as error:
        sys.exit(f"  cannot reach {BASE_URL} — is the service up? ({error.reason})")

    print(f"  HTTP {status}")
    pretty = json.dumps(json.loads(payload), indent=2)
    print("\n".join("  " + line for line in pretty.splitlines()))
    print()


def main() -> None:
    print(f"== mini-nucleiq smoke test against {BASE_URL} ==\n")

    print("-- happy path --")
    call("GET", "/health")
    call("POST", "/v1/analyze", {"sample": SAMPLE, "algorithms": ALGORITHMS})

    print("-- error cases (expected 400 / 404 / 422) --")
    call("POST", "/v1/analyze", {"sample": SAMPLE, "algorithms": ["does-not-exist"]})
    call("POST", "/v1/analyze", {"sample": "no-such-sample", "algorithms": ["even-zeroes"]})
    call("POST", "/v1/analyze", {"sample": SAMPLE, "algorithms": []})


if __name__ == "__main__":
    main()
