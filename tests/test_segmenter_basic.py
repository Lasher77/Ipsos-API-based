from __future__ import annotations

from app.rules_loader import FeatureRule, RuleSet
from app.segmenter import score_member


def _ruleset() -> RuleSet:
    return RuleSet(
        segments=["Alpha", "Beta"],
        intercepts={"Alpha": 0.0, "Beta": 0.0},
        thresholds={"core_threshold": 1.0, "mid_threshold": 0.5},
        features=[
            FeatureRule(
                feature_id="status==Active",
                input_field="status",
                match_value="Active",
                coefficients={"Alpha": 1.0, "Beta": 1.0},
            ),
            FeatureRule(
                feature_id="tier==Gold",
                input_field="tier",
                match_value="Gold",
                coefficients={"Alpha": 2.0, "Beta": 0.0},
            ),
        ],
        rule_set_version="test",
        case_insensitive=False,
    )


def test_tie_breaks_are_lexicographic() -> None:
    result = score_member({"status": "Active"}, _ruleset())
    assert result.segment == "Alpha"
    assert result.second_segment == "Beta"


def test_missing_field_defaults_to_zero() -> None:
    result = score_member({"status": "Inactive"}, _ruleset())
    assert result.best_score == 0.0
    assert result.type == "Rest"


def test_difference_and_type_logic() -> None:
    result = score_member({"status": "Active", "tier": "Gold"}, _ruleset())
    assert result.segment == "Alpha"
    assert result.second_segment == "Beta"
    assert result.difference == 2.0
    assert result.type == "Core"
