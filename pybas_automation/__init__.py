"""Default configuration for models."""
from pydantic import ConfigDict

from .settings import STORAGE_SUBDIR

default_model_config = ConfigDict(populate_by_name=True, extra="forbid", use_enum_values=True)

__all__ = ["default_model_config", "STORAGE_SUBDIR"]
