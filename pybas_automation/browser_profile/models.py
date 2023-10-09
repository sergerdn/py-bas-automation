"""Browser profile models."""

import json
from enum import Enum
from typing import Union

from pydantic import BaseModel, DirectoryPath, Field

from pybas_automation import STORAGE_SUBDIR, default_model_config
from pybas_automation.bas_actions.browser.proxy.models import BasActionBrowserProxy
from pybas_automation.browser_profile.settings import _proxy_filename, _user_data_dir_default_factory


class BrowserProfileProxyEnum(str, Enum):
    """Enum class for possible proxy types."""

    HTTP = "http"
    SOCKS5 = "socks5"


class BrowserProfileProxy(BaseModel):
    """Defines the proxy settings for a browser profile."""

    model_config = default_model_config

    hostname: str = Field(default=str)
    port: int = Field(default=3128, ge=1, le=65535)
    type: BrowserProfileProxyEnum = Field(default=BrowserProfileProxyEnum.SOCKS5)
    login: str = Field(default="", max_length=200)
    password: str = Field(default="", max_length=200)


class BrowserProfile(BaseModel):
    """Represents a browser profile with customizable settings."""

    model_config = default_model_config

    profile_dir: DirectoryPath = Field(default_factory=_user_data_dir_default_factory)
    fingerprint_raw: Union[str, None] = Field(default=None)
    proxy: Union[BrowserProfileProxy, None] = Field(default=None)

    def save_proxy_to_profile(self) -> bool:
        """
        Save the proxy to the profile directory.

        :return: True if the proxy was saved successfully, False otherwise.
        """

        if self.proxy is None:
            return False

        is_http: bool = self.proxy.type == BrowserProfileProxyEnum.HTTP

        bas_proxy = BasActionBrowserProxy(
            server=self.proxy.hostname,
            port=f"{self.proxy.port}",  # type: ignore
            is_http=is_http,  # type: ignore
            name=self.proxy.login,
            password=self.proxy.password,
        )

        sub_dir = self.profile_dir.joinpath(STORAGE_SUBDIR)
        sub_dir.mkdir(parents=True, exist_ok=True)

        proxy_filename = sub_dir.joinpath(_proxy_filename)
        proxy_filename.open("w", encoding="utf-8").write(json.dumps(bas_proxy.model_dump(by_alias=True)))

        return True
