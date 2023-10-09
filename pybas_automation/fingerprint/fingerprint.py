"""
Functions for getting fingerprints from the fingerprint API.
"""

from urllib.parse import urlencode

import httpx

from pybas_automation.fingerprint.models import BasFingerprintRequest

FINGERPRINT_BASE_URL = "https://fingerprints.bablosoft.com/prepare?version=5"


class FingerprintRequestException(Exception):
    """Raised when a fingerprint request fails."""


def get_fingerprint(
    request_data: BasFingerprintRequest,
) -> str:
    """Get a fingerprint for the given fingerprint key."""

    json_data = dict(request_data.model_dump())

    json_data["tags"] = ",".join(request_data.tags)
    json_data["returnpc"] = "true"

    url = f"{FINGERPRINT_BASE_URL}&{urlencode(json_data)}"

    response = httpx.get(url, timeout=10)
    if response.status_code != 200:
        raise FingerprintRequestException(f"Failed to get fingerprint: {response.text}")

    response_json_data = response.json()
    if not response_json_data.get("valid"):
        raise FingerprintRequestException(f"Failed to get fingerprint: {response_json_data}")

    return response.text.strip()
