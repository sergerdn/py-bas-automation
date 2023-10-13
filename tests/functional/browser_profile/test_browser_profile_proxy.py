import ipaddress
import time
from typing import Generator

import pycountry  # type: ignore
import pytest

from pybas_automation.bas_actions.browser.proxy.models import BasActionBrowserProxy
from pybas_automation.browser_profile.proxy import get_external_info_ip

countries = [c.alpha_2 for c in pycountry.countries]


class TestBrowserProfileProxy:
    @pytest.fixture(autouse=True)
    def run_around_tests(self) -> Generator[None, None, None]:
        import threading

        from tests.contrib.socks5_server.server import SOCKS5ProxyServer

        opts = {
            "auth": ("test_user", "test_pass"),
            "listen_ip": "127.0.0.1",
            "port": 9999,
            "bind_address": "0.0.0.0",
        }

        server = SOCKS5ProxyServer(opts)  # type: ignore

        def run_server(s) -> None:  # type: ignore
            print("Starting server")
            s.serve_forever()

        t = threading.Thread(
            target=run_server,
            name="socks5-server",
            args=[
                server,
            ],
        )
        t.start()
        time.sleep(1)
        # run tests
        yield
        # teardown
        server.shutdown()

    def test_proxy(self) -> None:
        proxy = BasActionBrowserProxy(
            server="127.0.0.1",
            port="9999",  # type: ignore
            is_http=False,  # type: ignore
            name="test_user",
            password="test_pass",
        )

        result = get_external_info_ip(proxy)
        assert result.get("ip", None) is not None
        assert result.get("country", None) is not None
        assert result.get("country", None) != ""

        ip = result.get("ip")
        # simple check that ip is valid
        ipaddress.ip_address(ip)  # type: ignore

        assert result.get("country") in countries

        print(result)
