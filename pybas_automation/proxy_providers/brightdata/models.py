"""
BrightData proxy provider models
"""

from pydantic import BaseModel, Field

from pybas_automation import default_model_config
from pybas_automation.bas_actions.browser.proxy import BasActionBrowserProxy, BasActionBrowserProxyTypeEnum
from pybas_automation.utils import random_string


class BrightdataCredentialsModel(BaseModel):
    """Brightdata credentials model."""

    model_config = default_model_config

    username: str
    password: str


class BrightDataProxyModel(BaseModel):
    """BrightData proxy model."""

    model_config = default_model_config

    hostname: str = Field(default="brd.superproxy.io")
    port: int = Field(default=22225)
    credentials: BrightdataCredentialsModel

    def to_bas_proxy(self, keep_session: bool = True) -> BasActionBrowserProxy:
        """
        Convert to BasActionBrowserProxy model.

        :param keep_session: If True, the proxy will be used with the same session to avoid ip changes.
        """

        login = self.credentials.username
        if keep_session:
            login = f"{login}-session-{random_string(10)}"

        return BasActionBrowserProxy(
            server=self.hostname,
            port=self.port,
            type=BasActionBrowserProxyTypeEnum.HTTP,
            login=login,
            password=self.credentials.password,
        )
