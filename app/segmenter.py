from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.rules_loader import FeatureRule, RuleSet
from app.utils import normalize_value


@dataclass(frozen=True)
class SegmentResult:
    segment: str
    second_segment: str | None
    type: str
    difference: float
    best_score: float
    second_best_score: float | None
    scores: dict[str, float]
    matched_features: list[dict[str, Any]] | None


def _compute_feature_value(
    member: dict[str, Any],
    rule: FeatureRule,
    case_insensitive: bool,
) -> int:
    raw_value = member.get(rule.input_field)
    normalized = normalize_value(raw_value, case_insensitive)
    if normalized is None:
        return 0
    match_value = normalize_value(rule.match_value, case_insensitive)
    return 1 if normalized == match_value else 0


def _round_scores(scores: dict[str, float], decimals: int = 4) -> dict[str, float]:
    return {segment: round(value, decimals) for segment, value in scores.items()}


def score_member(
    member: dict[str, Any],
    ruleset: RuleSet,
    include_features: bool = False,
    pretty_scores: bool = False,
) -> SegmentResult:
    scores = dict(ruleset.intercepts)
    matched_features: list[dict[str, Any]] = []

    for feature in ruleset.features:
        value = _compute_feature_value(member, feature, ruleset.case_insensitive)
        if value == 1:
            for segment, coeff in feature.coefficients.items():
                scores[segment] += coeff
        if include_features:
            matched_features.append(
                {
                    "feature_id": feature.feature_id,
                    "input_field": feature.input_field,
                    "match_value": feature.match_value,
                    "value": value,
                }
            )

    sorted_segments = sorted(scores.items(), key=lambda item: (-item[1], item[0]))
    best_segment, best_score = sorted_segments[0]
    second_segment = None
    second_best_score = None
    if len(sorted_segments) > 1:
        second_segment, second_best_score = sorted_segments[1]

    difference = best_score - second_best_score if second_best_score is not None else 0.0
    core_threshold = ruleset.thresholds["core_threshold"]
    mid_threshold = ruleset.thresholds["mid_threshold"]

    if difference > core_threshold:
        segment_type = "Core"
    elif mid_threshold < difference <= core_threshold:
        segment_type = "Mid"
    else:
        segment_type = "Rest"

    if pretty_scores:
        scores = _round_scores(scores)
        best_score = round(best_score, 4)
        if second_best_score is not None:
            second_best_score = round(second_best_score, 4)
        difference = round(difference, 4)

    return SegmentResult(
        segment=best_segment,
        second_segment=second_segment,
        type=segment_type,
        difference=difference,
        best_score=best_score,
        second_best_score=second_best_score,
        scores=scores,
        matched_features=matched_features if include_features else None,
    )
