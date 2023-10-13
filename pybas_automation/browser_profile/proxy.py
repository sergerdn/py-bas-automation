"""Browser profile proxy module."""

from typing import Dict

import httpx

from pybas_automation.bas_actions.browser.proxy.models import BasActionBrowserProxy


class ExternalIPRequestException(Exception):
    """Raised when an error occurs while requesting the external IP address."""


def get_external_info_ip(bas_proxy: BasActionBrowserProxy) -> Dict:
    """Get the external IP address."""

    proxy_str = f"{bas_proxy.server}:{bas_proxy.port}"

    if bas_proxy.name and bas_proxy.password:
        proxy_str = f"{bas_proxy.name}:{bas_proxy.password}@{proxy_str}"
    if bas_proxy.is_http:
        proxies = f"http://{proxy_str}"
    else:
        proxies = f"socks5://{proxy_str}"

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
