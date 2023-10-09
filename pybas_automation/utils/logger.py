"""
Return a logger named based on the caller's full module path.
"""

import inspect
import logging


def get_logger() -> logging.Logger:
    """
    Returns a logger named based on the caller's full module path.
    Format: "[<full-module-path>]"
    """

    # Get the module name of the caller.
    frame = inspect.stack()[1]
    module = inspect.getmodule(frame[0])

    if module is None:
        raise ValueError("Could not determine the caller's module.")

    logger_name = f"[{module.__name__}]"

    logger = logging.getLogger(logger_name)
    # Optional: Set the logging level and formatter, or any other logger configuration you want here.

    return logger
