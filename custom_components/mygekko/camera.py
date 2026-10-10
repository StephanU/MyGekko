"""Camera platform for MyGekko."""
import logging

import aiohttp
from homeassistant.components.camera import Camera
from homeassistant.components.camera import CameraEntityFeature
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from .pymygekko.resources.Cams import Cam
from .pymygekko.resources.Cams import CamFeature
from .pymygekko.resources.DoorInterComs import DoorInterCom
from .pymygekko.resources.DoorInterComs import DoorInterComFeature

from .entity import MyGekkoEntity


_LOGGER: logging.Logger = logging.getLogger(__name__)


async def async_setup_entry(hass, entry, async_add_devices):
    """Set up Camera platform."""
    coordinator = entry.runtime_data
    cams = coordinator.api.get_cams()
    if cams is not None:
        async_add_devices(MyGekkoCam(coordinator, cam) for cam in cams)
    door_inter_coms = coordinator.api.get_door_inter_coms()
    if door_inter_coms is not None:
        async_add_devices(MyGekkoInterComCam(coordinator, door_inter_com) for door_inter_com in door_inter_coms)


class MyGekkoInterComCam(MyGekkoEntity, Camera):
    """mygekko Door InterCom Camera class."""

    _attr_name = None

    def __init__(self, coordinator, door_inter_com: DoorInterCom):
        """Initialize the MyGekko Door InterCom camera."""
        super().__init__(coordinator, door_inter_com, "door_inter_com", "cam")
        Camera.__init__(self)

        self._door_inter_com = door_inter_com
        supported_features = self._door_inter_com.supported_features
        self._attr_supported_features = CameraEntityFeature(0)

        if DoorInterComFeature.STREAM in supported_features:
            self._attr_supported_features |= CameraEntityFeature.STREAM

    async def stream_source(self) -> str | None:
        """Return the source of the stream."""
        return self._door_inter_com.stream_url

    async def async_camera_image(
        self, width: int | None = None, height: int | None = None
    ) -> bytes | None:
        """Return bytes of camera image."""
        if self._door_inter_com.image_url:
            try:
                session = async_get_clientsession(self.hass, verify_ssl=False)
                async with session.get(
                    self._door_inter_com.image_url, timeout=aiohttp.ClientTimeout(total=10)
                ) as resp:
                    if resp.status != 200:
                        _LOGGER.error("Error fetching camera image from camera %s. Error: %s", self._door_inter_com.name, resp.reason)
                        return None
                    image_bytes = await resp.read()

                return image_bytes

            except (aiohttp.ClientError, TimeoutError) as err:
                _LOGGER.debug("Image fetch failed: %s", err)
                return None
        else:
            return None


class MyGekkoCam(MyGekkoEntity, Camera):
    """mygekko Camera class."""

    _attr_name = None

    def __init__(self, coordinator, cam: Cam):
        """Initialize the MyGekko cam."""
        super().__init__(coordinator, cam, "cam", "cam")
        Camera.__init__(self)

        self._cam = cam
        supported_features = self._cam.supported_features
        self._attr_supported_features = CameraEntityFeature(0)

        if CamFeature.STREAM in supported_features:
            self._attr_supported_features |= CameraEntityFeature.STREAM

    async def stream_source(self) -> str | None:
        """Return the source of the stream."""
        return self._cam.stream_url

    async def async_camera_image(
        self, width: int | None = None, height: int | None = None
    ) -> bytes | None:
        """Return bytes of camera image."""
        if self._cam.image_url:
            try:
                session = async_get_clientsession(self.hass, verify_ssl=False)
                async with session.get(
                    self._cam.image_url, timeout=aiohttp.ClientTimeout(total=10)
                ) as resp:
                    if resp.status != 200:
                        _LOGGER.error("Error fetching camera image from camera %s. Error: %s", self._cam.name, resp.reason)
                        return None
                    image_bytes = await resp.read()

                return image_bytes

            except (aiohttp.ClientError, TimeoutError) as err:
                _LOGGER.debug("Image fetch failed: %s", err)
                return None
        else:
            return None
