import ipaddress
import time
from typing import Generator

import pycountry  # type: ignore
import pytest

from pybas_automation.bas_actions.browser.proxy import BasActionBrowserProxy, BasActionBrowserProxyTypeEnum
from pybas_automation.browser_profile.proxy import get_external_info_ip

# Create a list of country codes using pycountry
countries = [c.alpha_2 for c in pycountry.countries]


class TestBrowserProfileProxy:
    @pytest.fixture(autouse=True)
    def run_around_tests(self) -> Generator[None, None, None]:
        """
        Setup and teardown fixture for the tests in this class. Starts and shuts down a SOCKS5 server.
        The server is run in a separate thread for the duration of the tests.
        """
        import threading

        from tests.contrib.socks5_server.server import SOCKS5ProxyServer

        # Configuration options for the SOCKS5 server
        opts = {
            "auth": ("test_user", "test_pass"),
            "listen_ip": "127.0.0.1",
            "port": 9999,
            "bind_address": "0.0.0.0",
        }

        server = SOCKS5ProxyServer(opts)  # type: ignore

        def run_server(s) -> None:  # type: ignore
            """Helper function to run the server."""
            print("Starting server")
            s.serve_forever()

        # Start the SOCKS5 server in a separate thread
        t = threading.Thread(
            target=run_server,
            name="socks5-server",
            args=[
                server,
            ],
        )
        t.start()
        # Give the server some time to start up
        time.sleep(1)

        # run tests
        yield

        # teardown and shutdown the server after tests
        server.shutdown()

    def test_proxy(self) -> None:
        """
        Test to verify the behavior and functionality of a proxy. This test asserts the validity of the
        returned IP and checks if the returned country code is known.
        """
        # Create a proxy configuration
        proxy = BasActionBrowserProxy(
            server="127.0.0.1",
            port=9999,
            type=BasActionBrowserProxyTypeEnum.SOCKS5,
            login="test_user",
            password="test_pass",
        )

        # Fetch external info through the proxy
        result = get_external_info_ip(proxy)
        # Ensure there is an IP and country in the response
        assert result.get("ip", None) is not None
        assert result.get("country", None) is not None
        assert result.get("country", None) != ""

        ip = result.get("ip")
        # Validate the IP address
        ipaddress.ip_address(ip)  # type: ignore

        # Check if the country returned is in the known countries list
        assert result.get("country") in countries

        print(result)
