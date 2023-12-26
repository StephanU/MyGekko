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

from .const import DOMAIN
from .entity import MyGekkoEntity


async def async_setup_entry(hass, entry, async_add_devices):
    """Set up cover platform."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    blinds = coordinator.api.get_blinds()
    if blinds is not None:
        async_add_devices(MyGekkoCover(coordinator, blind) for blind in blinds)


class MyGekkoCover(MyGekkoEntity, CoverEntity):
    """mygekko Cover class."""

    _attr_name = None
    _attr_device_class = CoverDeviceClass.SHUTTER

    def __init__(self, coordinator, blind: Blind):
        """Initialize the MyGekko cover."""
        super().__init__(coordinator, blind, "blinds")
        self._blind = blind
        supported_features = self._blind.supported_features
        self._attr_supported_features = 0

        if BlindFeature.OPEN_CLOSE in supported_features:
            self._attr_supported_features |= (
                CoverEntityFeature.OPEN | CoverEntityFeature.CLOSE
            )

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
        """Check whether the cover is closed."""
        # myGekko blinds are closed on 100 and open on 0
        return (
            ceil(self._blind.position) == 100
            if self._blind.position is not None
            else None
        )

    @property
    def current_cover_position(self) -> int | None:
        """Position of the cover."""
        # myGekko blinds are closed on 100 and open on 0
        return (
            (100 - int(self._blind.position))
            if self._blind.position is not None
            else None
        )

    @property
    def current_cover_tilt_position(self) -> int | None:
        """Tilt Position of the cover."""
        # myGekko blinds are closed on 100 and open on 0
        return (
            (100 - int(self._blind.tilt_position))
            if self._blind.tilt_position is not None
            else None
        )

    @property
    def is_closing(self) -> bool:
        """Check whether the cover is closing."""
        return (
            self._blind.state == BlindState.DOWN
            or self._blind.state == BlindState.HOLD_DOWN
        )

    @property
    def is_opening(self) -> bool:
        """Check whether the cover is opening."""
        return (
            self._blind.state == BlindState.UP
            or self._blind.state == BlindState.HOLD_UP
        )

    async def async_open_cover(self, **kwargs: Any):
        """Open the cover."""
        await self._blind.set_state(BlindState.HOLD_UP)

    async def async_close_cover(self, **kwargs: Any):
        """Close cover."""
        await self._blind.set_state(BlindState.HOLD_DOWN)

    async def async_stop_cover(self, **kwargs: Any):
        """Stop the cover."""
        await self._blind.set_state(BlindState.STOP)

    async def async_set_cover_position(self, **kwargs: Any) -> None:
        """Set the cover position."""
        # myGekko blinds are closed on 100 and open on 0
        await self._blind.set_position(100.0 - float(kwargs[ATTR_POSITION]))

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
        # myGekko blinds are closed on 100 and open on 0
        await self._blind.set_tilt_position(100.0 - float(kwargs[ATTR_TILT_POSITION]))
