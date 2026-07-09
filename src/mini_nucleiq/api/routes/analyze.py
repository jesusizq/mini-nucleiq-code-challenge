"""The versioned analysis endpoint."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends

from mini_nucleiq.api.dependencies import get_analyze_sample
from mini_nucleiq.api.dto import AnalyzeRequest, AnalyzeResponse
from mini_nucleiq.application.analyze_sample import AnalyzeSample

router = APIRouter(prefix="/v1", tags=["analysis"])


@router.post("/analyze")
def analyze(
    request: AnalyzeRequest,
    use_case: Annotated[AnalyzeSample, Depends(get_analyze_sample)],
) -> AnalyzeResponse:
    analysis = use_case.execute(request.sample, request.algorithms)
    return AnalyzeResponse.from_domain(analysis)
