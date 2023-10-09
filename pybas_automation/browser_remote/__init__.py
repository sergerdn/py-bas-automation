"""
Browser processes module.
"""

from .browser_remote import BrowserRemote, BrowserRemoteDebuggingPortNotAvailableError

__all__ = [
    "BrowserRemote",
    "BrowserRemoteDebuggingPortNotAvailableError",
]
