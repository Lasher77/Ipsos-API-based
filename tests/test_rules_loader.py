from __future__ import annotations

import json
from pathlib import Path

import pytest

from app.config import Settings
from app.rules_loader import RulesLoaderError, load_rules


def _write_rules(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload), encoding="utf-8")


def test_rules_loader_validates_required_fields(tmp_path: Path) -> None:
    rules_path = tmp_path / "rules.json"
    payload = {
        "segments": [{"id": 1, "name": "Segment A"}, {"id": 2, "name": "Segment B"}],
        "intercepts": {"seg1": 0.0, "seg2": 1.0},
        "type_thresholds": {"core_gt": 1.0, "mid_gt": 0.5},
        "rules": [
            {
                "crm_field": "status",
                "match_value": "Active",
                "coefficients": {"seg1": 0.1, "seg2": 0.2},
            }
        ],
        "rule_set_version": "test-version",
    }
    _write_rules(rules_path, payload)

    ruleset = load_rules(Settings(rules_path=rules_path))

    assert ruleset.segments == ["Segment A", "Segment B"]
    assert ruleset.intercepts["Segment A"] == 0.0
    assert ruleset.rule_set_version == "test-version"
    assert ruleset.features[0].feature_id == "status==Active"


def test_rules_loader_rejects_missing_intercepts(tmp_path: Path) -> None:
    rules_path = tmp_path / "rules.json"
    _write_rules(rules_path, {"segments": [], "type_thresholds": {"core_gt": 1.0, "mid_gt": 0.5}, "rules": []})

    with pytest.raises(RulesLoaderError):
        load_rules(Settings(rules_path=rules_path))
