"""Browser profile proxy module."""

from typing import Dict

import httpx

from pybas_automation.browser_profile.models import BrowserProfileProxy


class ExternalIPRequestException(Exception):
    """Raised when an error occurs while requesting the external IP address."""


def get_external_info_ip(profile_proxy: BrowserProfileProxy) -> Dict:
    """Get the external IP address."""

    proxy_str = f"{profile_proxy.hostname}:{profile_proxy.port}"

    if profile_proxy.login and profile_proxy.password:
        proxy_str = f"{profile_proxy.login}:{profile_proxy.password}@{proxy_str}"

    match profile_proxy.type:
        case "socks5":
            proxies = f"socks5://{proxy_str}"
        case "http":
            proxies = f"http://{proxy_str}"
        case _:
            raise ValueError(f"Invalid proxy type: {profile_proxy.type}")
    try:
        response = httpx.get(url="https://lumtest.com/myip.json", proxies=proxies, timeout=10)
    except Exception as exc:
        raise ExternalIPRequestException("Failed to get external IP.") from exc

    if response.status_code != 200:
        raise ExternalIPRequestException(f"Failed to get external IP: {response.text}")

    try:
        response_json_data = response.json()
    except Exception as exc:
        raise ExternalIPRequestException("Failed to get external IP.") from exc

    return dict(response_json_data)
