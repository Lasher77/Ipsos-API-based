from __future__ import annotations

from pathlib import Path
from typing import Optional

from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="SEGMENTER_", env_file=".env", extra="ignore")

    rules_path: Path = Field(default=Path("rules/bvmw_typing_tool_rules_v2.json"))
    case_insensitive: bool = Field(default=False)


class RuleSetMetadata(BaseModel):
    model_config = SettingsConfigDict(extra="ignore")

    rule_set_version: Optional[str] = None
    case_insensitive: Optional[bool] = None
