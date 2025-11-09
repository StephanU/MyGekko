"""Camera platform for MyGekko."""
import logging

import aiohttp
from homeassistant.components.camera import Camera
from homeassistant.components.camera import CameraEntityFeature
from homeassistant.core import callback
from PyMyGekko.resources.Cams import Cam
from PyMyGekko.resources.Cams import CamFeature
from PyMyGekko.resources.DoorInterComs import DoorInterCom
from PyMyGekko.resources.DoorInterComs import DoorInterComFeature

from .const import DOMAIN
from .entity import MyGekkoEntity


_LOGGER: logging.Logger = logging.getLogger(__name__)


async def async_setup_entry(hass, entry, async_add_devices):
    """Set up Camera platform."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
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
        self._attr_supported_features = 0

        if CamFeature.STREAM in supported_features:
            self._attr_supported_features |= DoorInterComFeature.STREAM

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        self.async_write_ha_state()

    async def stream_source(self) -> str | None:
        """Return the source of the stream."""
        return self._door_inter_com.stream_url

    async def async_camera_image(
        self, width: int | None = None, height: int | None = None
    ) -> bytes | None:
        """Return bytes of camera image."""
        if self._door_inter_com.image_url:
            try:
                async with aiohttp.ClientSession() as session, session.get(self._door_inter_com.image_url) as resp:
                    if resp.status != 200:
                        _LOGGER.error("Error fetching camera image from camera %s. Error: %s", self._door_inter_com.name, resp.msg)
                        return None
                    image_bytes = await resp.read()

                return image_bytes

            except Exception:
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
        self._attr_supported_features = 0

        if CamFeature.STREAM in supported_features:
            self._attr_supported_features |= CameraEntityFeature.STREAM

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        self.async_write_ha_state()

    async def stream_source(self) -> str | None:
        """Return the source of the stream."""
        return self._cam.stream_url

    async def async_camera_image(
        self, width: int | None = None, height: int | None = None
    ) -> bytes | None:
        """Return bytes of camera image."""
        if self._cam.image_url:
            try:
                async with aiohttp.ClientSession() as session, session.get(self._cam.image_url) as resp:
                    if resp.status != 200:
                        _LOGGER.error("Error fetching camera image from camera %s. Error: %s", self._cam.name, resp.msg)
                        return None
                    image_bytes = await resp.read()

                return image_bytes

            except Exception:
                return None
        else:
            return None
