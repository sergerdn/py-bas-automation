"""BasTask models."""

from uuid import UUID, uuid4

from pydantic import BaseModel, Field

from pybas_automation import default_model_config
from pybas_automation.bas_actions.browser.browser_settings.models import BasActionBrowserSettings


class BasTask(BaseModel):
    """A task contains all the information needed to run a task via BAS GUI."""

    model_config = default_model_config

    # unique task id
    task_id: UUID = Field(default_factory=uuid4)

    browser_settings: BasActionBrowserSettings = Field(default_factory=BasActionBrowserSettings)
