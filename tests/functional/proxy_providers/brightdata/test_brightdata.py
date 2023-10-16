from typing import Dict

from pybas_automation.proxy_providers.brightdata import BrightdataCredentialsModel, BrightDataProxyModel


class TestBrightdata:
    def test_basic(self, brightdata_credentials: Dict[str, str]) -> None:
        """Test the basic functionality of the Brightdata proxy provider."""

        # Extract the username and password from the provided credentials dictionary
        username, password = brightdata_credentials["username"], brightdata_credentials["password"]

        # Ensure the username and password are both not None
        assert username is not None
        assert password is not None

        # Create a BrightdataCredentialsModel object using the extracted credentials
        credentials = BrightdataCredentialsModel(username=username, password=password)

        # Initialize a BrightDataProxyModel object using the credentials
        proxy = BrightDataProxyModel(credentials=credentials)

        # Convert the proxy object to a bas_proxy format with keep_session set to False
        bas_proxy_1 = proxy.to_bas_proxy(keep_session=False)

        # Assert the proxy conversion is successful, and it does not contain a session in its login
        assert bas_proxy_1 is not None
        assert "-session-" not in bas_proxy_1.login  # type: ignore
