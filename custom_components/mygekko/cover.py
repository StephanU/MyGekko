"""Cover platform for MyGekko."""
from math import ceil
from typing import Any

from homeassistant.components.cover import ATTR_POSITION
from homeassistant.components.cover import ATTR_TILT_POSITION
from homeassistant.components.cover import CoverDeviceClass
from homeassistant.components.cover import CoverEntity
from homeassistant.components.cover import CoverEntityFeature
from homeassistant.core import callback
from PyMyGekko.resources.Blinds import Blind
from PyMyGekko.resources.Blinds import BlindFeature
from PyMyGekko.resources.Blinds import BlindState

from .const import COVER
from .const import DOMAIN
from .entity import MyGekkoEntity


async def async_setup_entry(hass, entry, async_add_devices):
    """Setup cover platform."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    blinds = coordinator.api.get_blinds()
    if blinds is not None:
        async_add_devices(MyGekkoCover(coordinator, blind) for blind in blinds)


class MyGekkoCover(MyGekkoEntity, CoverEntity):
    """mygekko Cover class."""

    _attr_device_class = CoverDeviceClass.SHUTTER

    def __init__(self, coordinator, blind: Blind):
        super().__init__(coordinator, blind, COVER)
        self._blind = blind
        supported_features = self._blind.supported_features
        self._attr_supported_features = 0

        if BlindFeature.OPEN_CLOSE_STOP in supported_features:
            self._attr_supported_features |= (
                CoverEntityFeature.OPEN
                | CoverEntityFeature.CLOSE
                | CoverEntityFeature.STOP
            )

        if BlindFeature.SET_POSITION in supported_features:
            self._attr_supported_features |= CoverEntityFeature.SET_POSITION

        if BlindFeature.SET_TILT_POSITION in supported_features:
            self._attr_supported_features |= (
                CoverEntityFeature.OPEN_TILT
                | CoverEntityFeature.CLOSE_TILT
                | CoverEntityFeature.STOP_TILT
                | CoverEntityFeature.SET_TILT_POSITION
            )

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        self.async_write_ha_state()

    @property
    def is_closed(self) -> bool | None:
        # myGekko blinds are closed on 100 and open on 0
        return ceil(self._blind.position) == 100

    @property
    def current_cover_position(self) -> int | None:
        """Position of the cover."""
        if self._blind.position is None:
            return None
        # myGekko blinds are closed on 100 and open on 0
        return 100 - int(self._blind.position)

    @property
    def current_cover_tilt_position(self) -> int | None:
        """Tilt Position of the cover."""
        if self._blind.tilt_position is None:
            return None
        # myGekko blinds are closed on 100 and open on 0
        return 100 - int(self._blind.tilt_position)

    @property
    def is_closing(self) -> bool:
        return (
            self._blind.state == BlindState.DOWN
            or self._blind.state == BlindState.HOLD_DOWN
        )

    @property
    def is_opening(self) -> bool:
        return (
            self._blind.state == BlindState.UP
            or self._blind.state == BlindState.HOLD_UP
        )

    async def async_open_cover(self, **kwargs: Any):
        """Open the cover."""
        await self._blind.set_position(0.0)

    async def async_close_cover(self, **kwargs: Any):
        """Close cover."""
        await self._blind.set_position(100.0)

    async def async_stop_cover(self, **kwargs: Any):
        """Stop the cover."""
        await self._blind.set_state(BlindState.STOP)

    async def async_set_cover_position(self, **kwargs: Any) -> None:
        await self._blind.set_position(float(kwargs[ATTR_POSITION]))

    async def async_open_cover_tilt(self, **kwargs: Any):
        """Open the cover."""
        await self._blind.set_tilt_position(0.0)

    async def async_close_cover_tilt(self, **kwargs: Any):
        """Close cover."""
        await self._blind.set_tilt_position(100.0)

    async def async_stop_cover_tilt(self, **kwargs: Any):
        """Stop the cover."""
        await self._blind.set_state(BlindState.STOP)

    async def async_set_cover_tilt_position(self, **kwargs: Any) -> None:
        """Move the cover tilt to a specific position."""
        await self._blind.set_tilt_position(float(kwargs[ATTR_TILT_POSITION]))
