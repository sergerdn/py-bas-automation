"""
Models for the browser_automator module.
"""

from typing import Annotated

from pydantic import BaseModel, UrlConstraints
from pydantic_core import Url

WebsocketUrl = Annotated[Url, UrlConstraints(allowed_schemes=["ws"])]


class WsUrlModel(BaseModel):
    ws_url: WebsocketUrl