from pydantic import BaseModel, Field


class ReviewResult(BaseModel):
    novelty: int = Field(..., description="Novelty score, range 1-10")
    methodological_rigour: int = Field(
        ..., description="Methodological rigour score, range 1-10"
    )
    result_credibility: int = Field(
        ..., description="Result credibility score, range 1-10"
    )
    writing_clarity: int = Field(
        ..., description="Writing clarity score, range 1-10"
    )
    total_score: int = Field(..., description="Overall score, range 1-10")
    justification: str = Field(
        ..., description="A brief review justification (2-3 sentences)"
    )