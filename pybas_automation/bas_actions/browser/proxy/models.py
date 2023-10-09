"""Browser / Proxy models."""

from typing import Optional

from pydantic import BaseModel, Field, field_validator

from pybas_automation import default_model_config


class BasActionBrowserProxy(BaseModel):
    """BasActionBrowserProxy is used to specify a proxy for a browser profile."""

    model_config = default_model_config

    server: str = Field(default="127.0.0.1")
    port: str = Field(default="3128", alias="Port")
    is_http: Optional[bool] = Field(alias="IsHttp", default=False)
    name: Optional[str] = Field(default="")
    password: Optional[str] = Field(default="")

    @field_validator("port")
    @classmethod
    def port_str_must_be_integer(cls, v: str) -> str:
        """Validate that port is an integer and in range 1-65535."""
        try:
            v_int = int(v)
        except ValueError as exc:
            raise ValueError(f"must be integer, got: {v}") from exc

        if v_int < 1 or v_int > 65535:
            raise ValueError(f"must be in range 1..65535, got: {v}")

        return v
