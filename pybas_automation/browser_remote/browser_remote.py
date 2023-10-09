"""Browser Processes module."""

import json
from typing import Union

import httpx
import websockets

from pybas_automation.utils import get_logger, timing

logger = get_logger()


class BrowserRemoteDebuggingPortNotAvailableError(Exception):
    """Raised when the remote debugging port is not available."""


def _url_to_ws_endpoint(endpoint_url: str) -> str:
    """Get the websocket url from the http endpoint url."""
    if endpoint_url.startswith("ws"):
        return endpoint_url

    logger.debug("<ws preparing> retrieving websocket url from %s", endpoint_url)

    http_url = endpoint_url if endpoint_url.endswith("/") else f"{endpoint_url}/"
    http_url += "json/version/"
    try:
        response = httpx.get(http_url)
    except httpx.ConnectError as exc:
        raise BrowserRemoteDebuggingPortNotAvailableError(
            f"Cannot connect to {http_url}.\n" "This does not look like a DevTools server, try connecting via ws://."
        ) from exc

    if response.status_code != 200:
        raise ValueError(
            f"Unexpected status {response.status_code} when connecting to {http_url}.\n"
            "This does not look like a DevTools server, try connecting via ws://."
        )

    json_data = json.loads(response.text)
    logger.debug("<ws preparing> response: %s", json_data)

    return str(json_data["webSocketDebuggerUrl"])


class BrowserRemote:
    """BrowserProcess is responsible for finding the browser process for a given profile folder path."""

    remote_debugging_port: int
    ws_endpoint: Union[str, None]
    browser_version: Union[str, None]

    def __init__(self, remote_debugging_port: int):
        """
        BrowserProcess instance.

        :param remote_debugging_port: CDP remote debugging port.
        """

        self.remote_debugging_port = remote_debugging_port
        self.ws_endpoint = None
        self.browser_version = None

    def __repr__(self) -> str:
        return f"<BrowserProcess remote_debugging_port={self.remote_debugging_port} ws_endpoint={self.ws_endpoint}>"

    @timing
    def find_ws(self) -> bool:
        """
        Find the websocket endpoint for the browser remote debugging url.

        :return: True if found.

        :raises BrowserRemoteDebuggingPortNotAvailableError: If the remote debugging port is not available.
        """

        if not self._get_ws_endpoint():
            return False

        return True

    def _get_ws_endpoint(self) -> Union[str, bool]:
        if not self.remote_debugging_port:
            return False

        url = f"http://localhost:{self.remote_debugging_port}"
        ws_url = _url_to_ws_endpoint(url)
        self.ws_endpoint = ws_url

        return True

    async def _get_browser_version(self, ws_url: str) -> dict:
        async with websockets.connect(ws_url) as ws:  # type: ignore
            # Send a command to get browser version
            payload = json.dumps({"id": 1, "method": "Browser.getVersion"})
            await ws.send(payload)
            response = await ws.recv()
            return dict(json.loads(response))
