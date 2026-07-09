"""Unversioned liveness endpoint for orchestrators (Docker/k8s healthchecks)."""

from __future__ import annotations

from fastapi import APIRouter

router = APIRouter(tags=["ops"])


@router.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
