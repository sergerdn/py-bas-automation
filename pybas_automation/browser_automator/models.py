"""
Models for the browser_automator module.
"""

from typing import Annotated, List

from pydantic import BaseModel, UrlConstraints
from pydantic_core import Url

WebsocketUrl = Annotated[Url, UrlConstraints(allowed_schemes=["ws"])]


class WsUrlModel(BaseModel):
    """WsUrlModel is a model for a WebSocket URL."""

    ws_url: WebsocketUrl


class StorageStateModel(BaseModel):
    cookies: List
    origins: List
    trust_tokens: List
