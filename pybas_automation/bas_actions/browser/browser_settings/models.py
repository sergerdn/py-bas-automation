"""Browser / Browser Settings models."""

from enum import Enum
from typing import List, Union

from pydantic import BaseModel, DirectoryPath, Field

from pybas_automation import default_model_config
from pybas_automation.bas_actions.browser.browser_settings import browser_command_line_factory
from pybas_automation.bas_actions.browser.proxy.models import BasActionBrowserProxy
from pybas_automation.bas_actions.fingerprint_switcher.apply_fingerprint.models import BasActionApplyFingerprintModel


class WidevineEnum(str, Enum):
    """Widevine settings model."""

    ENABLE = "enable"
    DISABLE = "disable"
    EMPTY = ""


class SafeBrowsingEnum(str, Enum):
    """Safe Browsing settings model."""

    ENABLE = "enable"
    DISABLE = "disable"
    EMPTY = ""


class ChromeComponentsEnum(str, Enum):
    """Chrome components settings model."""

    ENABLE = "enable"
    DISABLE = "disable"
    EMPTY = ""


class BasActionBrowserSettingsComponents(BaseModel):
    """Bas Browser components settings model."""

    model_config = default_model_config

    # Enable or disable Widevine plugin.
    # enable - Use Widevine
    # disable - Don't use Widevine
    # Empty string - Don't change this setting
    widevine: WidevineEnum = Field(default=WidevineEnum.ENABLE)

    # Enable Safe Browsing. It is technology embedded in Chrome, helps to protect users from malicious websites.
    # Its absence can be detected.
    # enable - Enable Safe Browsing
    # disable - Disable Safe Browsing
    # Empty string - Don't change this setting
    safe_browsing: SafeBrowsingEnum = Field(default=SafeBrowsingEnum.ENABLE)

    # Enable Chrome components. Increase profile size, but its absence can be detected.
    # enable - Enable components
    # disable - Disable components
    # Empty string - Don't change this setting
    components: ChromeComponentsEnum = Field(default=ChromeComponentsEnum.ENABLE)


class BasActionBrowserSettingsRendering(BaseModel):
    """Bas Browser rendering settings model."""

    model_config = default_model_config

    # Maximum times browser content can be rendered per one second.
    # The lower this value, the lower the CPU usage will be. Setting it too low may affect site operability.
    # Reducing it below 30 may lead to unpredictable consequences. Minimum value is 10.
    maximum_fps: int = Field(default=30, gt=10, lt=60)


class BasActionBrowserSettingsNetwork(BaseModel):
    """Bas Browser network settings model."""

    # Unlike HTTP, QUIC protocol is build on top of UDP. Not all proxies supports UDP.
    # It means that enabling QUIC can cause problems when working with certain proxies.
    # It is recommended to enable this option only if sure, that your proxy supports it. Disabled by default.
    # enable - Enable QUIC
    # disable - Disable QUIC
    enable_qiuc_protocol: bool = Field(default=True)


class BasActionBrowserSettingsProfile(BaseModel):
    """Bas Browser profile settings model."""

    model_config = default_model_config

    # String with profile folder. Slash type is not important. If folder doesn't exist, it will be created. If folder
    # already exists, BAS will use it as profile and restore all data from it like cookies, localstorage,
    # etc. By default, browser stores all profile data in temporary folder, you can use "temporary" keyword to switch
    # to new temporary profile. Empty string - Don't change temporary - Switch to new temporary profile
    profile_folder_path: DirectoryPath = Field(default="")

    # In case if profile folder already exists and has fingerprint data,
    # tells BAS to apply fingerprint used latest for that profile.
    always_load_fingerprint_from_profile_folder: bool = Field(default=False)

    # In case if profile folder already exists and has proxy data,
    # tells BAS to apply proxy used latest for that profile.
    always_load_proxy_from_profile_folder: bool = Field(default=False)


class BasActionBrowserSettings(BaseModel):
    """Browser / Browser Settings model."""

    model_config = default_model_config

    components: BasActionBrowserSettingsComponents = Field(default_factory=BasActionBrowserSettingsComponents)
    network: BasActionBrowserSettingsNetwork = Field(default_factory=BasActionBrowserSettingsNetwork)
    rendering: BasActionBrowserSettingsRendering = Field(default_factory=BasActionBrowserSettingsRendering)

    # Changes browser version for current thread.
    # This setting will restart browser and therefore reset all settings, so it is better to use it when thread starts.
    browser_version: str = Field(default="default")

    # Chromium command line arguments.
    command_line: Union[List[str]] = Field(default_factory=browser_command_line_factory)

    # Profile folder path.
    profile: BasActionBrowserSettingsProfile = Field(default_factory=BasActionBrowserSettingsProfile)

    # Proxy settings.
    proxy: Union[BasActionBrowserProxy, None] = Field(default=None)

    # Browser fingerprint. Fingerprint switcher -> Apply fingerprint
    fingerprint: BasActionApplyFingerprintModel = Field(default_factory=BasActionApplyFingerprintModel)
