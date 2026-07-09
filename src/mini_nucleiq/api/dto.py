"""Request/response DTOs for the HTTP edge (pydantic; validation lives here, not in the core)."""

from __future__ import annotations

from pydantic import BaseModel, Field, field_validator

from mini_nucleiq.domain.analysis import AnalysisResult, Verdict


class AnalyzeRequest(BaseModel):
    """A request to analyze one sample with one or more algorithms."""

    sample: str = Field(min_length=1)
    algorithms: list[str] = Field(
        min_length=1,  # empty list -> 422 (pydantic)
        description="One or more algorithm names; duplicates are ignored (first occurrence wins).",
    )

    @field_validator("algorithms")
    @classmethod
    def _drop_duplicates(cls, value: list[str]) -> list[str]:
        # Selecting an algorithm twice must not double its weight in the final rule;
        # collapse to first-occurrence order so the analysis is well-defined.
        return list(dict.fromkeys(value))


class AlgorithmResultDTO(BaseModel):
    """One algorithm's outcome as exposed over HTTP."""

    algorithm: str
    positive_cells: int
    positivity: float
    result: Verdict


class AnalyzeResponse(BaseModel):
    """The full analysis: per-algorithm outcomes plus the aggregated verdict."""

    sample: str
    algorithms: list[AlgorithmResultDTO]
    result: Verdict

    @classmethod
    def from_domain(cls, analysis: AnalysisResult) -> AnalyzeResponse:
        return cls(
            sample=analysis.sample_name,
            algorithms=[
                AlgorithmResultDTO(
                    algorithm=result.algorithm,
                    positive_cells=result.positive_cells,
                    # Rounded for display only; the verdict used exact arithmetic in the domain.
                    positivity=round(result.positivity, 2),
                    result=result.result,
                )
                for result in analysis.algorithms
            ],
            result=analysis.result,
        )
