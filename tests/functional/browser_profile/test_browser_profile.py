import json
import os

import pytest

from pybas_automation.bas_actions.browser.proxy import BasActionBrowserProxy, BasActionBrowserProxyTypeEnum
from pybas_automation.browser_profile import BrowserProfile, BrowserProfileStorage
from pybas_automation.fingerprint import BasFingerprintRequest, get_fingerprint


@pytest.mark.vcr()
class TestBrowserProfile:
    def test_save_fingerprint(self, fingerprint_key: str) -> None:
        """
        Test saving a browser fingerprint to a profile. The method
        verifies that the fingerprint is valid and can be saved
        successfully to the profile directory.
        """

        # Request and get a fingerprint based on the key
        request_data = BasFingerprintRequest(key=fingerprint_key)
        fingerprint_raw = get_fingerprint(request_data)

        # Ensure the received fingerprint is valid
        fingerprint_json = json.loads(fingerprint_raw)
        assert fingerprint_json.get("valid") is True

        # Create a browser profile with the obtained fingerprint
        browser_profile = BrowserProfile(fingerprint_raw=fingerprint_raw)
        assert browser_profile.profile_dir is not None

        # Save the browser profile using the storage utility
        browser_profile_storage = BrowserProfileStorage()
        browser_profile_storage.save(browser_profile=browser_profile)

        # Ensure the saved profile contains the fingerprint data
        assert os.path.exists(os.path.join(browser_profile.profile_dir, ".pybas", "fingerprint_raw.json")) is True

    def test_save_proxy(self) -> None:
        """
        Test saving a proxy configuration to a browser profile. The method
        ensures that the proxy details are saved correctly to the profile directory.
        """

        # Initialize an empty browser profile
        browser_profile = BrowserProfile()

        # Create a proxy configuration
        proxy = BasActionBrowserProxy(
            server="127.0.0.1",
            port=9999,
            type=BasActionBrowserProxyTypeEnum.HTTP,
            login="user",
            password="pass",
        )

        # Set and save the proxy configuration to the browser profile
        browser_profile.proxy = proxy
        result = browser_profile.save_proxy_to_profile()
        assert result is True
        assert os.path.exists(os.path.join(browser_profile.profile_dir, ".pybas", "proxy.json")) is True

    def test_save_all(self, fingerprint_key: str) -> None:
        """
        Test saving both fingerprint and proxy configurations to a browser profile.
        This method verifies that both configurations are saved correctly.
        """

        # Request and get a fingerprint based on the key
        request_data = BasFingerprintRequest(key=fingerprint_key)
        fingerprint_raw = get_fingerprint(request_data)

        # Ensure the received fingerprint is valid
        fingerprint_json = json.loads(fingerprint_raw)
        assert fingerprint_json.get("valid") is True

        # Create a browser profile with the obtained fingerprint
        browser_profile = BrowserProfile(fingerprint_raw=fingerprint_raw)
        assert browser_profile.profile_dir is not None

        # Create a proxy configuration
        proxy = BasActionBrowserProxy(
            server="127.0.0.1",
            port=31000,
            type=BasActionBrowserProxyTypeEnum.HTTP,
            login="user",
            password="pass",
        )

        # Set the proxy configuration to the browser profile
        browser_profile.proxy = proxy

        # Save the browser profile with both configurations using the storage utility
        browser_profile_storage = BrowserProfileStorage()
        browser_profile_storage.save(browser_profile=browser_profile)
