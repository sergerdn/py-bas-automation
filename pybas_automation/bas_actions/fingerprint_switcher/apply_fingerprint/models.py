"""FingerprintSwitcher / Apply fingerprint models."""

from pydantic import BaseModel, Field

from pybas_automation import default_model_config


class BasActionApplyFingerprintModel(BaseModel):
    """Fingerprint switcher -> Apply fingerprint."""

    model_config = default_model_config

    # If these settings is set to true, canvas will be enabled and noise will be added to all data returned from canvas.
    safe_canvas: bool = Field(default=True)

    # If these settings is set to true, PerfectCanvas replacement will be enabled. Fingerprint must contain
    # PerfectCanvas data in order to make it work. See "Get fingerprint" action for explanation.
    use_perfect_canvas: bool = Field(default=True)

    # If these settings is set to true, WebGL will be enabled, noise will be added to WebGL canvas and
    # your hardware properties, like video card vendor and renderer, will be changed
    safe_webgl: bool = Field(default=True)

    # If these settings is set to true, WebGL will be enabled, noise will be added to WebGL canvas and your hardware
    # properties, like video card vendor and renderer, will be changed
    safe_audio: bool = Field(default=True)

    # If these settings is set to true battery API will show different values for each thread, this prevents sites for
    # detecting your real identity. In case if device from which fingerprint was obtained doesn't have battery API,
    # 100% charge level will always be returned.
    safe_battery: bool = Field(default=True)

    # By default, browser searches for fonts only in system font folder. This may lead to inconsistencies during
    # fingerprint emulation if target fingerprint has more fonts than local system. Therefore, it is recommended to
    # download font pack with most popular fonts. This setting allows to use font pack if it is installed.
    # More info about font pack and download link can be found here: https://wiki.bablosoft.com/doku.php?id=fontpack
    use_font_pack: bool = Field(default=True)

    # If these settings is set to true, results of API which returns element coordinates will be updated to protect
    # against 'client rects' fingerprinting.
    safe_element_size: bool = Field(default=False)

    # Chrome browser has Sensor API, which allows to read data from devices like accelerometer, gyroscope or others.
    # Data from that devices is available only on mobile platforms. After checking this setting data for that devices
    # will be generated and replaced automatically. Enable this option in order to emulate mobile fingerprints more
    # precisely.
    emulate_sensor_api: bool = Field(default=True)

    # Allows to better emulate devices with higher pixel density. With this setting enabled, emulation will be done
    # in the most natural way. It means that browser will render the page in a bigger resolution, just like on real
    # device. The tradeoff is higher system resources usage, because you need to perform more calculations to render
    # a bigger picture. Javascript settings related to pixel density, for example devicePixelRatio, will be replaced
    # correctly regardless if this setting will be enabled or not.
    emulate_device_scale_factor: bool = Field(default=True)
