from __future__ import annotations

import logging
from typing import Any

from fastapi import Body, FastAPI, HTTPException, Query

from app.config import Settings
from app.model import BatchRequest, BatchResponse, HealthResponse, MetaResponse, SegmentResponse
from app.rules_loader import RuleSet, RulesLoaderError, load_rules
from app.segmenter import score_member

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_app(ruleset: RuleSet | None = None) -> FastAPI:
    app = FastAPI(title="BVMW Typing Tool Segmenter", version="1.0.0")

    if ruleset is None:
        settings = Settings()
        try:
            ruleset = load_rules(settings)
        except RulesLoaderError as exc:
            logger.error("Failed to load rules: %s", exc)
            raise RuntimeError(str(exc)) from exc

    @app.get("/health", response_model=HealthResponse)
    def health() -> HealthResponse:
        return HealthResponse()

    @app.get("/meta", response_model=MetaResponse)
    def meta() -> MetaResponse:
        return MetaResponse(
            segments=ruleset.segments,
            thresholds=ruleset.thresholds,
            feature_count=len(ruleset.features),
            rule_set_version=ruleset.rule_set_version,
        )

    @app.post("/segment", response_model=SegmentResponse)
    def segment(
        payload: Any = Body(...),
        include_features: bool = Query(default=False),
        pretty_scores: bool = Query(default=False),
    ) -> SegmentResponse:
        if not isinstance(payload, dict):
            raise HTTPException(status_code=400, detail="Request body must be a JSON object")
        result = score_member(
            payload,
            ruleset,
            include_features=include_features,
            pretty_scores=pretty_scores,
        )
        return SegmentResponse(
            **result.__dict__,
            rule_set_version=ruleset.rule_set_version,
        )

    @app.post("/segment/batch", response_model=BatchResponse)
    def segment_batch(
        payload: BatchRequest,
        include_features: bool = Query(default=False),
        pretty_scores: bool = Query(default=False),
    ) -> BatchResponse:
        results = []
        for item in payload.items:
            if not isinstance(item, dict):
                raise HTTPException(status_code=400, detail="Each item must be a JSON object")
            result = score_member(
                item,
                ruleset,
                include_features=include_features,
                pretty_scores=pretty_scores,
            )
            results.append(
                SegmentResponse(
                    **result.__dict__,
                    rule_set_version=ruleset.rule_set_version,
                )
            )
        return BatchResponse(results=results, rule_set_version=ruleset.rule_set_version)

    return app


app = create_app()
