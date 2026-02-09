from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from app.config import RuleSetMetadata, Settings
from app.utils import sha256_file


@dataclass(frozen=True)
class FeatureRule:
    feature_id: str
    input_field: str
    match_value: str
    coefficients: dict[str, float]


@dataclass(frozen=True)
class RuleSet:
    segments: list[str]
    intercepts: dict[str, float]
    thresholds: dict[str, float]
    features: list[FeatureRule]
    rule_set_version: str
    case_insensitive: bool
    code_mappings: dict[str, dict[str, str]]
    value_aliases: dict[str, dict[str, str]]


class RulesLoaderError(ValueError):
    pass


def _ensure_mapping(value: Any, field_name: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise RulesLoaderError(f"Expected '{field_name}' to be an object")
    return value


def _ensure_list(value: Any, field_name: str) -> list[Any]:
    if not isinstance(value, list):
        raise RulesLoaderError(f"Expected '{field_name}' to be an array")
    return value


def _build_segment_names(raw_segments: list[Any], intercept_keys: list[str]) -> dict[str, str]:
    id_to_name: dict[int, str] = {}
    name_set: set[str] = set()
    for segment in raw_segments:
        if isinstance(segment, dict):
            seg_id = segment.get("id")
            name = segment.get("name")
            if isinstance(seg_id, int) and isinstance(name, str):
                id_to_name[seg_id] = name
                name_set.add(name)
        elif isinstance(segment, str):
            name_set.add(segment)

    mapping: dict[str, str] = {}
    for key in intercept_keys:
        if key.startswith("seg") and key[3:].isdigit():
            seg_id = int(key[3:])
            if seg_id in id_to_name:
                mapping[key] = id_to_name[seg_id]
                continue
        if key in name_set:
            mapping[key] = key
        else:
            mapping[key] = key
    return mapping


def _load_code_mappings(path: Path, case_insensitive: bool) -> dict[str, dict[str, str]]:
    if not path.exists():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise RulesLoaderError(f"Code list file is not valid JSON: {exc}") from exc
    if not isinstance(payload, dict):
        raise RulesLoaderError("Code list file must be a JSON object")

    normalized: dict[str, dict[str, str]] = {}
    for field, mapping in payload.items():
        if not isinstance(field, str) or not isinstance(mapping, dict):
            raise RulesLoaderError("Code list mappings must be objects keyed by field name")
        field_name = field.strip()
        normalized[field_name] = {}
        for key, value in mapping.items():
            if not isinstance(key, str) or not isinstance(value, str):
                continue
            map_key = key.strip()
            map_value = value.strip()
            if case_insensitive:
                map_key = map_key.lower()
                map_value = map_value.lower()
            normalized[field_name][map_key] = map_value
    return normalized


def _build_value_aliases(case_insensitive: bool) -> dict[str, dict[str, str]]:
    aliases = {
        "Anrede": {
            "weiblich": "female",
        },
        "Gesetzlicher_Vertreter": {
            "ja": (
                "Sind Sie in Ihrem Unternehmen (mit-)verantwortlich für Mitgliedschaften in "
                "beispielsweise Unternehmens- oder Handelsverbänden, Interessenvertretungen etc.?"
            ),
        },
    }
    if not case_insensitive:
        return aliases
    normalized: dict[str, dict[str, str]] = {}
    for field, mapping in aliases.items():
        normalized[field] = {key.lower(): value.lower() for key, value in mapping.items()}
    return normalized


def load_rules(settings: Settings) -> RuleSet:
    path = settings.rules_path
    try:
        raw_text = path.read_text(encoding="utf-8")
    except FileNotFoundError as exc:
        raise RulesLoaderError(f"Rules file not found at {path}") from exc

    try:
        payload = json.loads(raw_text)
    except json.JSONDecodeError as exc:
        raise RulesLoaderError(f"Rules file is not valid JSON: {exc}") from exc

    metadata = RuleSetMetadata.model_validate(payload)
    rule_set_version = metadata.rule_set_version or payload.get("version")
    if not isinstance(rule_set_version, str) or not rule_set_version:
        rule_set_version = sha256_file(path)

    case_insensitive = metadata.case_insensitive
    if case_insensitive is None:
        case_insensitive = settings.case_insensitive

    code_mappings = _load_code_mappings(settings.code_list_path, case_insensitive)
    value_aliases = _build_value_aliases(case_insensitive)

    intercepts_raw = _ensure_mapping(payload.get("intercepts"), "intercepts")
    intercept_keys = list(intercepts_raw.keys())
    if not intercept_keys:
        raise RulesLoaderError("No intercepts found in rules")

    raw_segments = _ensure_list(payload.get("segments", []), "segments")
    segment_name_map = _build_segment_names(raw_segments, intercept_keys)
    segments = [segment_name_map[key] for key in intercept_keys]

    intercepts: dict[str, float] = {}
    for key, value in intercepts_raw.items():
        if not isinstance(value, (int, float)):
            raise RulesLoaderError(f"Intercept for '{key}' must be a number")
        intercepts[segment_name_map[key]] = float(value)

    thresholds_raw = _ensure_mapping(payload.get("type_thresholds"), "type_thresholds")
    core_threshold = thresholds_raw.get("core_gt")
    mid_threshold = thresholds_raw.get("mid_gt")
    if not isinstance(core_threshold, (int, float)) or not isinstance(mid_threshold, (int, float)):
        raise RulesLoaderError("type_thresholds must include numeric 'core_gt' and 'mid_gt'")

    rules_raw = _ensure_list(payload.get("rules"), "rules")
    features: list[FeatureRule] = []
    for rule in rules_raw:
        if not isinstance(rule, dict):
            raise RulesLoaderError("Each rule must be an object")
        input_field = rule.get("crm_field") or rule.get("input_field")
        match_value = rule.get("match_value")
        coefficients_raw = _ensure_mapping(rule.get("coefficients"), "coefficients")
        if not isinstance(input_field, str) or not isinstance(match_value, str):
            raise RulesLoaderError("Each rule must include string 'crm_field'/'input_field' and 'match_value'")
        if set(coefficients_raw.keys()) != set(intercept_keys):
            raise RulesLoaderError(
                f"Coefficients for '{input_field}' must include keys {sorted(intercept_keys)}"
            )
        coefficients: dict[str, float] = {}
        for seg_key, coeff in coefficients_raw.items():
            if not isinstance(coeff, (int, float)):
                raise RulesLoaderError(f"Coefficient for '{seg_key}' must be a number")
            coefficients[segment_name_map[seg_key]] = float(coeff)
        feature_id = f"{input_field}=={match_value}"
        features.append(
            FeatureRule(
                feature_id=feature_id,
                input_field=input_field,
                match_value=match_value,
                coefficients=coefficients,
            )
        )

    return RuleSet(
        segments=segments,
        intercepts=intercepts,
        thresholds={"core_threshold": float(core_threshold), "mid_threshold": float(mid_threshold)},
        features=features,
        rule_set_version=rule_set_version,
        case_insensitive=case_insensitive,
        code_mappings=code_mappings,
        value_aliases=value_aliases,
    )
