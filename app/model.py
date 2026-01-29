from __future__ import annotations

from typing import Any, Optional

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
    second_segment: Optional[str]
    type: str
    difference: float
    best_score: float
    second_best_score: Optional[float]
    scores: dict[str, float]
    matched_features: Optional[list[dict[str, Any]]] = None
    rule_set_version: str


class BatchRequest(BaseModel):
    items: list[dict[str, Any]] = Field(default_factory=list)


class BatchResponse(BaseModel):
    results: list[SegmentResponse]
    rule_set_version: str
