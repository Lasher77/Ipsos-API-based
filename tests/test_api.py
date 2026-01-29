from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import create_app
from app.rules_loader import FeatureRule, RuleSet


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
                coefficients={"Alpha": 1.0, "Beta": 0.2},
            )
        ],
        rule_set_version="test",
        case_insensitive=False,
    )


def test_health_endpoint() -> None:
    client = TestClient(create_app(_ruleset()))
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_segment_endpoint_schema() -> None:
    client = TestClient(create_app(_ruleset()))
    response = client.post("/segment", json={"status": "Active"})
    assert response.status_code == 200
    payload = response.json()
    assert payload["segment"] == "Alpha"
    assert "scores" in payload
    assert payload["rule_set_version"] == "test"
