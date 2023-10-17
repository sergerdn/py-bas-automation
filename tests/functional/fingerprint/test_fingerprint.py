import json

import pytest

from pybas_automation.fingerprint import get_fingerprint
from pybas_automation.fingerprint.models import BasFingerprintRequest


@pytest.mark.vcr()
class TestFingerprint:
    def test_get_fingerprint(self, fingerprint_key: str) -> None:
        """Test the functionality of the `get_fingerprint` method."""

        # Ensure the provided fingerprint_key is not None or empty
        assert fingerprint_key not in [None, ""]

        # Prepare the request data using the given fingerprint_key
        request_data = BasFingerprintRequest(key=fingerprint_key)

        # Fetch the raw fingerprint using the `get_fingerprint` method
        fingerprint_raw = get_fingerprint(request_data)

        # Load the raw fingerprint as a JSON object
        fingerprint_json = json.loads(fingerprint_raw)

        # Validate that the fingerprint data is marked as valid
        assert fingerprint_json.get("valid") is True

        # Further assertions to verify the structure and content of the fetched fingerprint
        assert type(fingerprint_json.get("width", None)) is int  # Ensure width is an integer value
        assert type(fingerprint_json.get("height", None)) is int  # Ensure height is an integer value
        assert type(fingerprint_json.get("perfectcanvas", None)) is dict  # Ensure perfectcanvas is a dictionary
