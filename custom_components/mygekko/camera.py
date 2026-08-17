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
from yarl import URL

from .const import DOMAIN
from .entity import MyGekkoEntity


_LOGGER: logging.Logger = logging.getLogger(__name__)

IMAGE_TIMEOUT = aiohttp.ClientTimeout(total=10)


async def _async_fetch_camera_image(image_url: str, camera_name: str) -> bytes | None:
    """Fetch a camera image, supporting basic and digest auth credentials in the URL."""
    url = URL(image_url)
    auth = None
    if url.user is not None:
        # aiohttp rejects requests that combine an auth argument with
        # credentials embedded in the URL, so strip them from the URL.
        auth = aiohttp.BasicAuth(url.user, url.password or "")
        url = url.with_user(None)

    try:
        async with aiohttp.ClientSession(
            timeout=IMAGE_TIMEOUT
        ) as session, session.get(url, auth=auth) as resp:
            if resp.status == 200:
                return await resp.read()
            www_authenticate = resp.headers.get("WWW-Authenticate", "")
            needs_digest = (
                resp.status == 401
                and auth is not None
                and www_authenticate.lower().startswith("digest")
            )
            if not needs_digest:
                _LOGGER.error(
                    "Error fetching camera image from camera %s: HTTP %s",
                    camera_name,
                    resp.status,
                )
                return None

        # The camera only accepts digest auth (e.g. Axis cameras), retry with it.
        digest_auth = aiohttp.DigestAuthMiddleware(auth.login, auth.password)
        async with aiohttp.ClientSession(
            timeout=IMAGE_TIMEOUT, middlewares=(digest_auth,)
        ) as session, session.get(url) as resp:
            if resp.status != 200:
                _LOGGER.error(
                    "Error fetching camera image from camera %s with digest auth: HTTP %s",
                    camera_name,
                    resp.status,
                )
                return None
            return await resp.read()
    except (aiohttp.ClientError, TimeoutError) as err:
        _LOGGER.error(
            "Error fetching camera image from camera %s: %s", camera_name, err
        )
        return None


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
        self._attr_supported_features = CameraEntityFeature(0)

        if DoorInterComFeature.STREAM in supported_features:
            self._attr_supported_features |= CameraEntityFeature.STREAM

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
            return await _async_fetch_camera_image(
                self._door_inter_com.image_url, self._door_inter_com.name
            )
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
            return await _async_fetch_camera_image(self._cam.image_url, self._cam.name)
        return None
