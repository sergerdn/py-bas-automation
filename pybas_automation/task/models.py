"""Module for the BasTask model."""

from typing import Union
from uuid import UUID, uuid4

from pydantic import BaseModel, Field

from pybas_automation import default_model_config
from pybas_automation.bas_actions.browser.browser_settings.models import BasActionBrowserSettings


class BasTask(BaseModel):
    """
    Represents a task for BAS (Browser Automation Studio).

    This model holds all the essential details required to execute
    a task through the BAS GUI.
    """

    model_config = default_model_config
    # Unique identifier for the task
    task_id: UUID = Field(default_factory=uuid4)
    # Port number, updated when task is invoked by a BAS compiled script
    remote_debugging_port: Union[int, None] = None

    # Browser settings associated with the task
    browser_settings: BasActionBrowserSettings = Field(default_factory=BasActionBrowserSettings)
