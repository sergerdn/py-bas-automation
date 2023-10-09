import json
import os

import pytest

from pybas_automation.browser_profile import (BrowserProfile, BrowserProfileProxy, BrowserProfileProxyEnum,
                                              BrowserProfileStorage)
from pybas_automation.fingerprint import BasFingerprintRequest, get_fingerprint
from tests.functional.browser_profile.browser_base import BrowserProfileBase


@pytest.mark.vcr()
class TestBrowserProfile(BrowserProfileBase):
    def test_save_fingerprint(self, fingerprint_key: str) -> None:
        request_data = BasFingerprintRequest(key=fingerprint_key)
        fingerprint_raw = get_fingerprint(request_data)

        fingerprint_json = json.loads(fingerprint_raw)
        assert fingerprint_json.get("valid") is True

        browser_profile = BrowserProfile(fingerprint_raw=fingerprint_raw)
        assert browser_profile.profile_dir is not None

        browser_profile_storage = BrowserProfileStorage()
        browser_profile_storage.save(browser_profile=browser_profile)

        assert os.path.exists(os.path.join(browser_profile.profile_dir, ".pybas", "fingerprint_raw.json")) is True

    def test_save_proxy(self) -> None:
        browser_profile = BrowserProfile()
        proxy = BrowserProfileProxy(
            hostname="127.0.0.1", port=3128, type=BrowserProfileProxyEnum.SOCKS5, login="user", password="pass"
        )
        browser_profile.proxy = proxy
        result = browser_profile.save_proxy_to_profile()
        assert result is True
        assert os.path.exists(os.path.join(browser_profile.profile_dir, ".pybas", "proxy.json")) is True

    def test_save_all(self, fingerprint_key: str) -> None:
        request_data = BasFingerprintRequest(key=fingerprint_key)
        fingerprint_raw = get_fingerprint(request_data)

        fingerprint_json = json.loads(fingerprint_raw)
        assert fingerprint_json.get("valid") is True

        browser_profile = BrowserProfile(fingerprint_raw=fingerprint_raw)
        assert browser_profile.profile_dir is not None

        proxy = BrowserProfileProxy(
            hostname="127.0.0.1", port=3100, type=BrowserProfileProxyEnum.SOCKS5, login="user", password="pass"
        )

        browser_profile.proxy = proxy

        browser_profile_storage = BrowserProfileStorage()
        browser_profile_storage.save(browser_profile=browser_profile)
