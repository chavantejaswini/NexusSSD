"""Request/response schemas for the prediction endpoint."""

from __future__ import annotations

from pydantic import BaseModel, Field, model_validator


class PredictRequest(BaseModel):
    drive_id: int | None = Field(default=None, description="Score this drive's latest window")
    features: dict[str, float] | None = Field(
        default=None, description="Raw feature vector (alternative to drive_id)"
    )

    @model_validator(mode="after")
    def _one_of(self) -> "PredictRequest":
        if (self.drive_id is None) == (self.features is None):
            raise ValueError("provide exactly one of 'drive_id' or 'features'")
        return self


class FeatureContribution(BaseModel):
    name: str
    value: float
    importance: float


class PredictResponse(BaseModel):
    drive_id: int | None = None
    failure_probability: float
    band: str
    model_version: str
    horizon_days: int
    top_features: list[FeatureContribution]
