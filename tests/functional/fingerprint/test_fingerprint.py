import json

import pytest

from pybas_automation.fingerprint import get_fingerprint
from pybas_automation.fingerprint.models import BasFingerprintRequest


@pytest.mark.vcr()
class TestFingerprint:
    def test_get_fingerprint(self, fingerprint_key: str) -> None:
        assert fingerprint_key not in [None, ""]
        request_data = BasFingerprintRequest(key=fingerprint_key)
        fingerprint_raw = get_fingerprint(request_data)

        fingerprint_json = json.loads(fingerprint_raw)
        assert fingerprint_json.get("valid") is True

        assert fingerprint_json.get("valid") is True
        assert type(fingerprint_json.get("width", None)) is int
        assert type(fingerprint_json.get("height", None)) is int
        assert type(fingerprint_json.get("perfectcanvas", None)) is dict
