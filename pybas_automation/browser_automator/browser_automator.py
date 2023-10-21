"""
This module provides:

1. The `BrowserAutomator` class, simplifying web automation via the Chrome Developer Protocol (CDP).

2. Integration with the BAS_SAFE internal API for secure management of functions and properties within
   the BAS_SAFE environment, ensuring reliable execution of critical operations such as simulating mouse movements.
"""

import json
from typing import Any, Dict, List, Tuple, Union

import filelock
import httpx
from playwright.async_api import Browser, BrowserContext, CDPSession, Locator, Page
from playwright.async_api import Playwright as AsyncPlaywright
from playwright.async_api import async_playwright

from pybas_automation.browser_automator.cdp_client import CDPClient
from pybas_automation.browser_automator.models import WebsocketUrl, WsUrlModel
from pybas_automation.browser_profile import BrowserProfile
from pybas_automation.utils import get_logger

logger = get_logger()


class BrowserWsConnectError(Exception):
    """Exception raised when unable to connect to the browser's remote debugging port."""


def _url_to_ws_endpoint(endpoint_url: str) -> str:
    """
    Convert an HTTP endpoint URL to a WebSocket endpoint URL.

    :param endpoint_url: HTTP endpoint URL.
    :return: WebSocket endpoint URL.

    :raises BrowserWsConnectError: If unable to connect to the HTTP endpoint URL.
    """
    if endpoint_url.startswith("ws"):
        return endpoint_url

    logger.debug("Preparing WebSocket: retrieving WebSocket URL from %s", endpoint_url)

    http_url = endpoint_url if endpoint_url.endswith("/") else f"{endpoint_url}/"
    http_url += "json/version/"
    try:
        response = httpx.get(http_url)
    except httpx.ConnectError as exc:
        raise BrowserWsConnectError(
            f"Cannot connect to {http_url}. This may not be a DevTools server. Consider connecting via ws://."
        ) from exc

    if response.status_code != 200:
        raise ValueError(
            f"Unexpected status {response.status_code} when connecting to {http_url}. "
            "This might not be a DevTools server. Consider connecting via ws://."
        )

    json_data = json.loads(response.text)
    logger.debug("WebSocket preparation response: %s", json_data)

    return str(json_data["webSocketDebuggerUrl"])


async def _elem_coordinates(elem: Locator) -> Tuple[int, int]:
    """
    Get the coordinates of the given element.
    :param elem: The element to get the coordinates for.

    :raises ValueError: If unable to fetch bounding box for the given element.

    :return: The coordinates of the given element.
    """

    bounding_box = await elem.bounding_box()
    if not bounding_box:
        raise ValueError(f"Unable to fetch bounding box for element: {elem}")

    # Calculate the coordinates for the click (center of the element)
    x = int(bounding_box["x"] + bounding_box["width"] / 2)
    y = int(bounding_box["y"] + bounding_box["height"] / 2)
    return x, y


class BrowserAutomator:
    """
    A Python class for simplifying web automation by connecting to and interacting with web browsers
    through the Chrome Developer Protocol (CDP).

    This class provides a user-friendly and streamlined interface built on top of the core CDP commands,
    making it easier to automate browser actions and extract information from web pages.

    Additionally, it seamlessly integrates with the BAS_SAFE internal API, enhancing security and reliability
    within the BAS_SAFE environment. This integration extends to various actions, such as retrieving page source,
    simulating mouse movements, and more (Note: Not all functions are currently supported).
    """

    ws_endpoint: WsUrlModel
    remote_debugging_port: int

    browser_profile: BrowserProfile
    browser_version: Union[str, None]
    pw: AsyncPlaywright
    browser: Browser
    context: BrowserContext
    page: Page
    cdp_client: CDPClient
    cdp_session: CDPSession

    unique_process_id: Union[str, None]
    _javascript_code: str

    _lock: filelock.FileLock

    def __init__(
        self, browser_profile: BrowserProfile, remote_debugging_port: int, unique_process_id: Union[str, None] = None
    ):
        """
        Initialize the BrowserAutomator instance.

        :param browser_profile: The browser profile to use.
        :param remote_debugging_port: The remote debugging port to connect to.
        :param unique_process_id: A unique identifier for the `Worker.exe` process. Retrieved from the command line.
        """

        self.browser_profile = browser_profile
        self.remote_debugging_port = int(remote_debugging_port)
        if unique_process_id:
            self.unique_process_id = unique_process_id
            self._javascript_code = f"location.reload['_bas_hide_{unique_process_id}']"
        else:
            self.unique_process_id = None

    def get_ws_endpoint(self) -> str:
        """
        Return the WebSocket endpoint URL.

        :return: WebSocket endpoint URL.
        """
        return self.ws_endpoint.ws_url.unicode_string()

    def connect(self) -> None:
        """
        Connect to the browser via the WebSocket protocol.
        """
        ws_endpoint_url = _url_to_ws_endpoint(f"http://localhost:{self.remote_debugging_port}")
        self.ws_endpoint = WsUrlModel(ws_url=WebsocketUrl(ws_endpoint_url))
        self.cdp_client = CDPClient(self.ws_endpoint)

    async def __aexit__(self, *args: Any) -> None:
        """Asynchronous exit method to stop the Playwright instance."""
        if self.pw:
            await self.pw.stop()

    async def _get_browser_version(self) -> None:
        """
        Fetch and set the browser version from the WebSocket endpoint.

        :raises ValueError: If unable to retrieve the browser version from the WebSocket endpoint.
        """

        data = await self.cdp_client.send_command("Browser.getVersion")

        product_version = data.get("product", None)
        if not product_version:
            raise ValueError("Unable to fetch browser version")

        self.browser_version = product_version

    async def _fetch_attached_sessions(self) -> List[Dict]:
        """
        Retrieve a list of attached session information from the WebSocket endpoint.

        :return: List of attached session information.
        :raises ValueError: If unable to retrieve the attached sessions from the WebSocket endpoint.
        """

        data = await self.cdp_client.send_command("Target.getTargets")

        if not data.get("targetInfos", None):
            raise ValueError("Unable to fetch attached sessions")

        return [target_info for target_info in data["targetInfos"] if target_info["attached"]]

    async def _prepare_cdp(self) -> None:
        # Enables network tracking, network events will now be delivered to the client.
        await self.cdp_session.send("Network.setCacheDisabled", params={"cacheDisabled": False})
        # https://chromedevtools.github.io/devtools-protocol/tot/DOMStorage/#method-enable
        await self.cdp_session.send("DOMStorage.enable")

    async def __aenter__(self) -> "BrowserAutomator":
        """
        Asynchronous enter method to initialize the connection and retrieve session details.

        :return: BrowserAutomator instance.
        :raises BrowserWsConnectError: If unable to connect to the browser's remote debugging port.
        """

        self.connect()

        await self._get_browser_version()
        logger.info("Retrieved browser version: %s", self.browser_version)

        self.pw = await async_playwright().start()
        self.browser = await self.pw.chromium.connect_over_cdp(self.ws_endpoint.ws_url.unicode_string())
        self.context = self.browser.contexts[0]
        self.page = self.context.pages[0]

        # Fetch the attached sessions
        sessions = await self._fetch_attached_sessions()
        logger.debug("Attached sessions retrieved: %s", sessions)

        self.cdp_session: CDPSession = await self.context.new_cdp_session(self.page)
        await self._prepare_cdp()

        logger.debug("Successfully connected to browser: %s", self.browser)

        return self

    async def _bas_safe_call(self, page: Page, javascript_func_code: str) -> Any:
        """
        Call a JavaScript function in the BAS _SAFE internal API.

        :param page: The current page.
        :param javascript_func_code: The JavaScript function code to execute.

        :raises ValueError: If the self.unique_process_id is not set.

        :return: The result of the JavaScript function call.
        """

        if not self.unique_process_id:
            raise ValueError("You should set self.unique_process_id to use BAS_SAFE API")

        return await page.evaluate(javascript_func_code)

    async def bas_get_page_content(self, page: Union[Page, None] = None) -> Any:
        """
        Get the current page content.

        :param page: The current page.

        :raises ValueError: If the self.unique_process_id is not set.

        :return: The current page content.
        """

        if page is None:
            page = self.page

        javascript_func_code = f"{self._javascript_code}['BrowserAutomationStudio_GetPageContent']()"
        return await self._bas_safe_call(page=page, javascript_func_code=javascript_func_code)

    async def bas_scroll_mouse_to_coordinates(self, x: int, y: int, page: Union[Page, None] = None) -> Any:
        """
        Click on the given coordinates.

        :param x: The x coordinate.
        :param y: The y coordinate.
        :param page: The current page.

        :raises ValueError: If the self.unique_process_id is not set.
        """

        if page is None:
            page = self.page

        javascript_func_code = f"{self._javascript_code}['BrowserAutomationStudio_ScrollToCoordinates']({x},{y},true)"
        return await self._bas_safe_call(page=page, javascript_func_code=javascript_func_code)

    async def bas_move_mouse_to_elem(self, elem: Locator, page: Union[Page, None] = None) -> Any:
        """
        Move the mouse to the given element.

        :param elem: The element to move the mouse to.
        :param page: The current page.

        :raises ValueError: If the self.unique_process_id is not set.

        :return: The result of the JavaScript function call.
        """

        if page is None:
            page = self.page

        x, y = await _elem_coordinates(elem=elem)

        result = await self.bas_scroll_mouse_to_coordinates(x=x, y=y, page=page)
        logger.debug("Scrolled to coordinates: %s", result)
        return result
