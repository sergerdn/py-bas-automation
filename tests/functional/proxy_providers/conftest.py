import os
from typing import Dict

import pytest


@pytest.fixture(scope="module")
def brightdata_credentials() -> Dict[str, str]:
    username = os.environ.get("BRIGHTDATA_USERNAME", None)
    password = os.environ.get("BRIGHTDATA_PASSWORD", None)
    if username is None or password is None:
        raise ValueError("BRIGHTDATA_USERNAME or BRIGHTDATA_PASSWORD not set")

    return {"username": username, "password": password}
