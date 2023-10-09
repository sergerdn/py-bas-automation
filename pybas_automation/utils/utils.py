"""
Utility functions for the application.
"""

from functools import wraps
from time import time

from pybas_automation.utils import get_logger

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
