"""
Settings for the browser profile.
"""

import tempfile

from pydantic import DirectoryPath, FilePath

from pybas_automation.utils import create_storage_dir_in_app_data

_storage_dir = DirectoryPath("PyBASProfiles")
_fingerprint_raw_filename = FilePath("fingerprint_raw.json")
_proxy_filename = FilePath("proxy.json")

_filelock_filename = FilePath("tasks.lock")


def _user_data_dir_default_factory() -> FilePath:
    """Return the default user data directory."""

    profiles_dir = create_storage_dir_in_app_data(storage_dir=_storage_dir)

    if not profiles_dir.exists():
        profiles_dir.mkdir()

    profile_name = tempfile.mkdtemp(dir=profiles_dir)
    return FilePath(profile_name)
