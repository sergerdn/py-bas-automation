from pydantic import BaseModel, Field

from pybas_automation import default_model_config
from pybas_automation.bas_actions.browser.proxy.models import BasActionBrowserProxy
from pybas_automation.utils import random_string


class BrightdataCredentialsModel(BaseModel):
    model_config = default_model_config

    username: str
    password: str


class BrightDataProxyModel(BaseModel):
    model_config = default_model_config

    hostname: str = Field(default="brd.superproxy.io")
    port: int = Field(default=22225)
    credentials: BrightdataCredentialsModel

    def to_bas_proxy(self, keep_session: bool = True) -> BasActionBrowserProxy:
        login = self.credentials.username
        if keep_session:
            login = f"{login}-session-{random_string(10)}"

        return BasActionBrowserProxy(
            server=self.hostname,
            port=f"{self.port}",  # type: ignore
            is_http=True,  # type: ignore
            name=login,
            password=self.credentials.password,
        )
