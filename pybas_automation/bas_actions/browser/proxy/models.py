"""Browser / Proxy models."""
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field, field_validator

from pybas_automation import default_model_config


class BasActionBrowserProxyTypeEnum(str, Enum):
    """BasActionBrowserProxyTypeEnum is used to specify the type of proxy."""

    HTTP = "http"
    SOCKS5 = "socks5"
    AUTO = "auto"


class BasActionBrowserProxy(BaseModel):
    """BasActionBrowserProxy is used to specify a proxy for a browser profile."""

    model_config = default_model_config

    server: str = Field(default="127.0.0.1")
    port: int
    type: BasActionBrowserProxyTypeEnum = Field(default=BasActionBrowserProxyTypeEnum.HTTP)
    login: Optional[str] = Field(default="")
    password: Optional[str] = Field(default="")

    @field_validator("port")
    @classmethod
    def port_str_must_be_integer(cls, v: int) -> int:
        """Validate that port is an  in range 1-65535."""

        if v < 1 or v > 65535:
            raise ValueError(f"must be in range 1..65535, got: {v}")

        return v
