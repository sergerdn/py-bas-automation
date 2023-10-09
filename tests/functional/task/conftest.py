import os
import shutil
import tempfile
from typing import Generator

import pytest
from pydantic import DirectoryPath


@pytest.fixture(scope="function")
def storage_dir() -> Generator[DirectoryPath, None, None]:
    dir_name = DirectoryPath(tempfile.mkdtemp(prefix="pybas-storage_dir_test_"))
    if not os.path.exists(dir_name):
        os.mkdir(dir_name)

    yield DirectoryPath(dir_name)

    shutil.rmtree(dir_name, ignore_errors=True)


@pytest.fixture(scope="function")
def profiles_dir() -> Generator[DirectoryPath, None, None]:
    dir_name = DirectoryPath(tempfile.mkdtemp(prefix="pybas-profiles_dir_test_"))
    if not os.path.exists(dir_name):
        os.mkdir(dir_name)

    yield DirectoryPath(dir_name)

    shutil.rmtree(dir_name, ignore_errors=True)
