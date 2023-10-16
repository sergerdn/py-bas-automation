import os
import shutil
import tempfile
from typing import Generator

import pytest
from pydantic import DirectoryPath


@pytest.fixture(scope="function")
def storage_dir() -> Generator[DirectoryPath, None, None]:
    # Create a temporary directory with a specific prefix
    dir_name = DirectoryPath(tempfile.mkdtemp(prefix="pybas-storage_dir_test_"))

    # Make sure the directory exists
    if not os.path.exists(dir_name):
        os.mkdir(dir_name)

    # Yield the temporary directory for use in the tests
    yield DirectoryPath(dir_name)

    # Cleanup: Remove the temporary directory after tests are done
    shutil.rmtree(dir_name, ignore_errors=True)


@pytest.fixture(scope="function")
def profiles_dir() -> Generator[DirectoryPath, None, None]:
    # Create a temporary directory with a specific prefix
    dir_name = DirectoryPath(tempfile.mkdtemp(prefix="pybas-profiles_dir_test_"))

    # Make sure the directory exists
    if not os.path.exists(dir_name):
        os.mkdir(dir_name)

    # Yield the temporary directory for use in the tests
    yield DirectoryPath(dir_name)

    # Cleanup: Remove the temporary directory after tests are done
    shutil.rmtree(dir_name, ignore_errors=True)
