"""
Utility functions for the application.
"""
import random
import string
from functools import wraps
from time import time

from pybas_automation.utils.logger import get_logger

logger = get_logger()


def timing(f):  # type: ignore
    """Time functions for debugging purposes."""

    @wraps(f)
    def wrap(*args, **kw):  # type: ignore
        ts = time()
        result = f(*args, **kw)
        te = time()
        # pylint: disable=logging-fstring-interpolation
        logger.debug(f"func:{f.__name__} args:[{args}, {kw}] took: {te - ts:.4f} sec")

        return result

    return wrap


def random_string(length: int = 10) -> str:
    """
    Generate a random string.

    :param length: The length of the string.
    """

    return "".join(random.choices(string.ascii_lowercase + string.digits, k=length))
