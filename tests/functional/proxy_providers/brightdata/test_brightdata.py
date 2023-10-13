from typing import Dict

from pybas_automation.proxy_providers.brightdata import BrightdataCredentialsModel, BrightDataProxyModel


class TestBrightdata:
    def test_basic(self, brightdata_credentials: Dict[str, str]) -> None:
        username, password = brightdata_credentials["username"], brightdata_credentials["password"]
        assert username is not None
        assert password is not None

        credentials = BrightdataCredentialsModel(username=username, password=password)

        proxy = BrightDataProxyModel(credentials=credentials)

        bas_proxy_1 = proxy.to_bas_proxy(keep_session=False)
        assert bas_proxy_1 is not None
        assert "-session-" not in bas_proxy_1.login  # type: ignore
