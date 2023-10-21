"""
CDPClient is a wrapper around the Chrome DevTools Protocol (CDP) that allows sending commands to the browser.
"""
import json
from typing import Any, Dict, Optional

import websockets

from pybas_automation.browser_automator.models import WsUrlModel
from pybas_automation.utils import get_logger

logger = get_logger()


class CDPClient:
    """CDPClient is a wrapper around the Chrome DevTools Protocol (CDP) that allows sending commands to the browser."""

    ws_endpoint: WsUrlModel
    message_id: int

    def __init__(self, ws_endpoint: WsUrlModel):
        """
        Initialize CDPClient.
        :param ws_endpoint: The WebSocket endpoint URL.
        """

        self.ws_endpoint = ws_endpoint
        self.message_id = 0

    async def send_command(self, method: str, params: Optional[Dict[str, Any]] = None) -> Dict:
        """
        Send a command to the browser via CDP.

        :param method: The CDP method to call.
        :param params: The parameters to pass to the CDP method.
        """
        url = self.ws_endpoint.ws_url.unicode_string()

        async with websockets.connect(url) as ws:  # type: ignore
            self.message_id += 1
            message = {
                "id": self.message_id,
                "method": method,
                "params": params or {},
            }

            logger.debug("Sending message: %s", message)

            await ws.send(json.dumps(message))

            # Wait for the response
            response = await ws.recv()
            if response is None:
                raise ValueError("Unable to fetch response")

            data = json.loads(response)
            logger.debug("Received message: %s", data)

            if not data.get("result"):
                raise ValueError(f"Unable to fetch result: {data}")

            return dict(data.get("result"))
