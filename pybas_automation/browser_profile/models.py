"""Browser profile models."""

import json
from typing import Union

from pydantic import BaseModel, DirectoryPath, Field

from pybas_automation import STORAGE_SUBDIR, default_model_config
from pybas_automation.bas_actions.browser.proxy import BasActionBrowserProxy
from pybas_automation.browser_profile.settings import _proxy_filename, _user_data_dir_default_factory


class BrowserProfile(BaseModel):
    """Represents a browser profile with customizable settings."""

    model_config = default_model_config

    profile_dir: DirectoryPath = Field(default_factory=_user_data_dir_default_factory)
    fingerprint_raw: Union[str, None] = Field(default=None)
    proxy: Union[BasActionBrowserProxy, None] = Field(default=None)

    def save_proxy_to_profile(self) -> bool:
        """
        Save the proxy to the profile directory.

        :return: True if the proxy was saved successfully, False otherwise.
        """

        if self.proxy is None:
            return False

        bas_proxy = BasActionBrowserProxy(
            server=self.proxy.server,
            port=self.proxy.port,
            type=self.proxy.type,
            login=self.proxy.login,
            password=self.proxy.password,
        )

        sub_dir = self.profile_dir.joinpath(STORAGE_SUBDIR)
        sub_dir.mkdir(parents=True, exist_ok=True)

        proxy_filename = sub_dir.joinpath(_proxy_filename)
        proxy_filename.open("w", encoding="utf-8").write(json.dumps(bas_proxy.model_dump(mode="json")))

        return True
