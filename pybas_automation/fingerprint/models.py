"""Models for the BAS fingerprint API."""

from typing import List

from pydantic import BaseModel, Field

from pybas_automation import default_model_config


def tags_default_factory() -> List[str]:
    """Return the default tags for a fingerprint request."""

    return ["Microsoft Windows", "Chrome"]


class BasFingerprintRequest(BaseModel):
    """BasFingerprintRequest is used to request a fingerprint from the BAS fingerprint API."""

    model_config = default_model_config

    key: str = Field(min_length=64, max_length=64)
    tags: List[str] = Field(default_factory=tags_default_factory)
    min_browser_version: int = Field(default=117, ge=117)
    min_width: int = Field(default=1366)
    min_height: int = Field(default=768)
    max_width: int = Field(default=1920)
    max_height: int = Field(default=1080)
