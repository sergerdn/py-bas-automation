import os
import platform
import socket
from contextlib import closing

from dotenv import load_dotenv

# Get the absolute path to the root project directory.
ABS_PATH = os.path.normpath(os.path.join(os.path.dirname(__file__), ".."))

# Determine the path to the '.env' file within the root project directory.
dotenv_path = os.path.join(ABS_PATH, ".env")

# Load environment variables from '.env' file if it exists.
if os.path.exists(dotenv_path):
    load_dotenv(dotenv_path=dotenv_path)

# Check if the current operating system is Windows.
is_windows = platform.system().lower() == "windows"

# Define the path to the fixtures directory used in tests.
FIXTURES_DIR = os.path.join(ABS_PATH, "tests", "fixtures")

# Ensure the fixtures directory exists; if not, this will raise an AssertionError.
assert os.path.exists(FIXTURES_DIR)


def _find_free_port() -> int:
    """
    Finds and returns a free port on the local machine.

    This function will bind a new socket to an arbitrary free port and return
    the port number before closing the socket. This method is useful to get
    a port for temporary use (e.g., for testing purposes).

    :return: An integer representing the free port number.
    """
    with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as s:
        s.bind(("", 0))
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        return int(s.getsockname()[1])
