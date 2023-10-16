import json
import os

import pytest

from pybas_automation.browser_profile import BrowserProfile, BrowserProfileStorage


@pytest.mark.vcr()
class TestBrowserProfileStorage:
    def test_create_no_fingerprint(self, fingerprint_key: str) -> None:
        """Test the creation of a browser profile without providing a fingerprint."""

        # Create a browser profile storage
        browser_profile_storage = BrowserProfileStorage(fingerprint_key=fingerprint_key)
        assert browser_profile_storage.count() == 0

        # Create a new browser profile
        browser_profile = browser_profile_storage.new()
        # Ensure the profile directory exists and has been created
        assert browser_profile.profile_dir.is_dir() is True
        assert browser_profile.profile_dir.exists() is True
        assert browser_profile_storage.count() == 1

        # Ensure the fingerprint file has been created inside the profile directory
        fingerprint_filename = browser_profile.profile_dir.joinpath(".pybas", "fingerprint_raw.json")
        assert fingerprint_filename.exists() is True

    def test_create_with_fingerprint(self, fingerprint_str: str) -> None:
        """Test the creation of a browser profile with a provided fingerprint."""

        browser_profile_storage = BrowserProfileStorage()
        assert browser_profile_storage.count() == 0
        browser_profile = browser_profile_storage.new(fingerprint_raw=fingerprint_str)
        # Ensure the profile directory exists
        assert browser_profile.profile_dir.is_dir() is True
        assert browser_profile.profile_dir.exists() is True

        # Ensure the fingerprint file exists inside the profile directory
        fingerprint_filename = browser_profile.profile_dir.joinpath(".pybas", "fingerprint_raw.json")
        assert fingerprint_filename.exists() is True

    def test_create_with_profile_name(self, fingerprint_key: str, fingerprint_str: str) -> None:
        """Test the creation of a browser profile with a custom profile name."""

        browser_profile_storage = BrowserProfileStorage(fingerprint_key=fingerprint_key)
        assert browser_profile_storage.count() == 0

        # Create a new profile with a custom name
        browser_profile = browser_profile_storage.new(profile_name="cool_profile")

        # Ensure the profile directory has the correct name
        assert os.path.basename(browser_profile.profile_dir) == "cool_profile"
        assert browser_profile.profile_dir.is_dir() is True
        assert browser_profile.profile_dir.exists() is True
        assert browser_profile_storage.count() == 1

        # Ensure the fingerprint file exists inside the profile directory
        fingerprint_filename = browser_profile.profile_dir.joinpath(".pybas", "fingerprint_raw.json")
        assert fingerprint_filename.exists() is True

    def test_load(self, fingerprint_str: str) -> None:
        """Test loading profiles from storage."""

        browser_profile_storage = BrowserProfileStorage()
        assert browser_profile_storage.count() == 0
        # Create multiple browser profiles
        for num in range(0, 10):
            browser_profile = browser_profile_storage.new(
                fingerprint_raw=fingerprint_str, profile_name=f"cool_profile_{num}"
            )
            assert browser_profile.profile_dir.is_dir() is True
            assert browser_profile_storage.count() == 1 + num

        # Load the profiles from a new storage instance
        new_browser_profile_storage = BrowserProfileStorage()

        assert new_browser_profile_storage.count() == 10
        profiles = new_browser_profile_storage.load_all()

        assert len(profiles) == 10

    def test_serialize_deserialize(self, fingerprint_key: str, fingerprint_str: str) -> None:
        """Test serialization and deserialization of a browser profile."""

        browser_profile_storage = BrowserProfileStorage()

        browser_profile = browser_profile_storage.new(fingerprint_raw=fingerprint_str, profile_name="cool_profile_1")

        # Serialize the profile object
        serialized = json.dumps(browser_profile.model_dump(mode="json"))
        assert serialized is not None

        # Deserialize the serialized data back into a profile object
        deserialized = BrowserProfile(**json.loads(serialized))
        assert deserialized is not None
