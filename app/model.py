from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: str = "ok"


class MetaResponse(BaseModel):
    segments: list[str]
    thresholds: dict[str, float]
    feature_count: int
    rule_set_version: str


class SegmentResponse(BaseModel):
    segment: str
    second_segment: str | None
    type: str
    difference: float
    best_score: float
    second_best_score: float | None
    scores: dict[str, float]
    matched_features: list[dict[str, Any]] | None = None
    rule_set_version: str


class BatchRequest(BaseModel):
    items: list[dict[str, Any]] = Field(default_factory=list)


class BatchResponse(BaseModel):
    results: list[SegmentResponse]
    rule_set_version: str
