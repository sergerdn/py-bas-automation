import os
import platform
import socket
import unittest
from contextlib import closing

from dotenv import load_dotenv

ABS_PATH = os.path.normpath(os.path.join(os.path.dirname(__file__), ".."))  # root project directory
dotenv_path = os.path.join(ABS_PATH, ".env")
if os.path.exists(dotenv_path):
    load_dotenv(dotenv_path=dotenv_path)

is_windows = platform.system().lower() == "windows"
windows_test = unittest.skipIf(is_windows, "OS not supported: %s" % platform.system())

FIXTURES_DIR = os.path.join(ABS_PATH, "tests", "fixtures")
assert os.path.exists(FIXTURES_DIR)


def _find_free_port() -> int:
    with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as s:
        s.bind(("", 0))
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        return int(s.getsockname()[1])
