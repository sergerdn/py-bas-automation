import json
import os

import pytest

from pybas_automation.browser_profile import BrowserProfile, BrowserProfileStorage
from tests.functional.browser_profile.browser_base import BrowserProfileBase


@pytest.mark.vcr()
class TestBrowserProfileStorage(BrowserProfileBase):
    def test_create_no_fingerprint(self, fingerprint_key: str) -> None:
        browser_profile_storage = BrowserProfileStorage(fingerprint_key=fingerprint_key)
        assert browser_profile_storage.count() == 0

        browser_profile = browser_profile_storage.new()
        assert browser_profile.profile_dir.is_dir() is True
        assert browser_profile.profile_dir.exists() is True
        assert browser_profile_storage.count() == 1

        fingerprint_filename = browser_profile.profile_dir.joinpath(".pybas", "fingerprint_raw.json")
        assert fingerprint_filename.exists() is True

    def test_create_with_fingerprint(self, fingerprint_str: str) -> None:
        browser_profile_storage = BrowserProfileStorage()
        assert browser_profile_storage.count() == 0
        browser_profile = browser_profile_storage.new(fingerprint_raw=fingerprint_str)
        assert browser_profile.profile_dir.is_dir() is True
        assert browser_profile.profile_dir.exists() is True

        fingerprint_filename = browser_profile.profile_dir.joinpath(".pybas", "fingerprint_raw.json")
        assert fingerprint_filename.exists() is True

    def test_create_with_profile_name(self, fingerprint_key: str, fingerprint_str: str) -> None:
        browser_profile_storage = BrowserProfileStorage(fingerprint_key=fingerprint_key)
        assert browser_profile_storage.count() == 0

        browser_profile = browser_profile_storage.new(profile_name="cool_profile")

        assert os.path.basename(browser_profile.profile_dir) == "cool_profile"
        assert browser_profile.profile_dir.is_dir() is True
        assert browser_profile.profile_dir.exists() is True
        assert browser_profile_storage.count() == 1

        fingerprint_filename = browser_profile.profile_dir.joinpath(".pybas", "fingerprint_raw.json")
        assert fingerprint_filename.exists() is True

    def test_load(self, fingerprint_str: str) -> None:
        browser_profile_storage = BrowserProfileStorage()
        assert browser_profile_storage.count() == 0
        for num in range(0, 10):
            browser_profile = browser_profile_storage.new(
                fingerprint_raw=fingerprint_str, profile_name=f"cool_profile_{num}"
            )
            assert browser_profile.profile_dir.is_dir() is True
            assert browser_profile_storage.count() == 1 + num

        new_browser_profile_storage = BrowserProfileStorage()

        assert new_browser_profile_storage.count() == 10
        profiles = new_browser_profile_storage.load_all()

        assert len(profiles) == 10

    def test_serialize_deserialize(self, fingerprint_key: str, fingerprint_str: str) -> None:
        browser_profile_storage = BrowserProfileStorage()

        browser_profile = browser_profile_storage.new(fingerprint_raw=fingerprint_str, profile_name="cool_profile_1")

        serialized = json.dumps(browser_profile.model_dump(mode="json"))
        assert serialized is not None

        deserialized = BrowserProfile(**json.loads(serialized))
        assert deserialized is not None
