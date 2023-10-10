"""
Browser storage module.

This module is responsible for storing browser profiles to disk and  loading metadata of browser profiles from disk
into memory.
"""

import os
import tempfile
from typing import List, Union

import filelock
from pydantic import DirectoryPath

from pybas_automation import STORAGE_SUBDIR
from pybas_automation.browser_profile.models import BrowserProfile
from pybas_automation.browser_profile.settings import _filelock_filename, _fingerprint_raw_filename, _storage_dir
from pybas_automation.fingerprint import BasFingerprintRequest, get_fingerprint
from pybas_automation.utils import create_storage_dir_in_app_data, get_logger

logger = get_logger()


class BrowserProfileStorageExistsError(Exception):
    """Raised when a browser profile already exists in the storage."""


class FingerprintError(Exception):
    """Raised when a fingerprint key is empty."""


class BrowserProfileStorage:
    """Handles the storage and retrieval of browser profiles."""

    storage_dir: DirectoryPath
    fingerprint_key: Union[str, None]

    _profiles: Union[list[BrowserProfile], None] = None
    _lock: filelock.FileLock

    def __init__(
        self, storage_dir: Union[DirectoryPath, None] = None, fingerprint_key: Union[str, None] = None
    ) -> None:
        """
        Initialize BrowserStorage.

        :param storage_dir: The directory to store the browser profiles.
        :param fingerprint_key: Your personal fingerprint key of FingerprintSwitcher.

        :raises ValueError: If the storage_dir is not a directory.
        """

        if storage_dir is None:
            self.storage_dir = create_storage_dir_in_app_data(storage_dir=_storage_dir)
        else:
            if not os.path.isdir(storage_dir):
                raise ValueError(f"storage_dir is not a directory: {storage_dir}")
            self.storage_dir = DirectoryPath(storage_dir)

        self.fingerprint_key = fingerprint_key
        self._lock = filelock.FileLock(os.path.join(self.storage_dir, _filelock_filename))

    def count(self) -> int:
        """
        Count the number of browser profiles in the storage.

        :return: The number of browser profiles in the storage.
        """

        return len(os.listdir(self.storage_dir))

    def new(self, profile_name: Union[str, None] = None, fingerprint_raw: Union[str, None] = None) -> BrowserProfile:
        """
        Create a new browser profile.

        :param profile_name: The name of the browser profile.
        :param fingerprint_raw: The fingerprint raw string.

        :return: BrowserProfile instance.

        :raises FingerprintKeyEmptyError: If the fingerprint key is empty.
        """

        if self.fingerprint_key is None and fingerprint_raw is None:
            raise FingerprintError("fingerprint_key is required.")

        if fingerprint_raw is not None and self.fingerprint_key is not None:
            raise FingerprintError("fingerprint_key and fingerprint_raw cannot be used together.")

        if profile_name is None:
            profile_dir = DirectoryPath(tempfile.mkdtemp(dir=str(self.storage_dir)))
        else:
            profile_dir = self.storage_dir.joinpath(profile_name)
            if profile_dir.exists():
                raise BrowserProfileStorageExistsError(f"Browser profile already exists: {profile_dir}")
            profile_dir.mkdir(parents=False)

        browser_profile = BrowserProfile(profile_dir=profile_dir)

        if fingerprint_raw is None:
            if self.fingerprint_key is None:  # is this dead code?
                raise FingerprintError("fingerprint_key is required.")

            request_data = BasFingerprintRequest(key=self.fingerprint_key)
            fingerprint_raw = get_fingerprint(request_data)

        browser_profile.fingerprint_raw = fingerprint_raw

        self.save(browser_profile=browser_profile)

        return browser_profile

    def save(self, browser_profile: BrowserProfile) -> None:
        """
        Save the browser profile to disk.

        :param browser_profile: BrowserProfile instance.
        :return: None.
        """

        sub_dir = browser_profile.profile_dir.joinpath(STORAGE_SUBDIR)
        sub_dir.mkdir(parents=True, exist_ok=True)

        fingerprint_filename = sub_dir.joinpath(_fingerprint_raw_filename)

        if browser_profile.fingerprint_raw is not None:
            fingerprint_filename.open("w", encoding="utf-8").write(browser_profile.fingerprint_raw)

    def load(self, profile_name: str) -> BrowserProfile:
        """
        Load a browser profile from disk.

        :param profile_name: The name of the browser profile.
        :return: BrowserProfile instance.
        """
        raise NotImplementedError()

    def load_all(self) -> List[BrowserProfile]:
        """
        Load all browser profiles from disk.

        :return: List[BrowserProfile].
        """
        if self._profiles is None:
            self._profiles = []

        for profile_name in os.listdir(self.storage_dir):
            profile_dir = self.storage_dir.joinpath(profile_name)
            browser_profile = BrowserProfile(profile_dir=profile_dir)

            sub_dir = profile_dir.joinpath(STORAGE_SUBDIR)

            fingerprint_filename = sub_dir.joinpath(_fingerprint_raw_filename)
            if fingerprint_filename.exists():
                fingerprint_raw = fingerprint_filename.open("r", encoding="utf-8").read()
                browser_profile.fingerprint_raw = fingerprint_raw

            self._profiles.append(browser_profile)

        return self._profiles
