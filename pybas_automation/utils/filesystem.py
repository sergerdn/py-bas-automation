"""
Filesystem utilities.
"""

import os

from pydantic import DirectoryPath


def create_storage_dir_in_app_data(storage_dir: DirectoryPath) -> DirectoryPath:
    """
    Create a storage directory in the local app data directory.

    :param storage_dir: The name of the storage directory.
    :return: Directory path to the created storage directory in the local app data directory.
    """

    _env_path = os.getenv("LOCALAPPDATA")
    if not _env_path:
        raise ValueError("Environment variable LOCALAPPDATA is not set.")

    local_app_data_path = DirectoryPath(_env_path)

    if not local_app_data_path.is_dir() or not local_app_data_path.exists():
        raise ValueError("Cannot find local app data path.")

    storage_dir = local_app_data_path.joinpath(storage_dir)
    if not storage_dir.exists():
        os.mkdir(storage_dir)

    return DirectoryPath(storage_dir)
