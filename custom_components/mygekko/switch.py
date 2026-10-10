"""Switch platform for MyGekko."""
from __future__ import annotations

from homeassistant.components.switch import SwitchEntity
from .api import EMobil
from .api import EMobilChargeState
from .api import Load
from .api import LoadState

from .entity import MyGekkoEntity


PARALLEL_UPDATES = 1


async def async_setup_entry(hass, entry, async_add_devices):
    """Set up switch platform."""
    coordinator = entry.runtime_data
    loads = coordinator.api.get_loads()
    if loads is not None:
        async_add_devices(MyGekkoSwitch(coordinator, load) for load in loads)
    emobils = coordinator.api.get_emobils()
    if emobils is not None:
        async_add_devices(MyGekkoEMobilChargeSwitch(coordinator, e) for e in emobils)


class MyGekkoSwitch(MyGekkoEntity, SwitchEntity):
    """mygekko Switch class."""

    _attr_name = None

    def __init__(self, coordinator, load: Load):
        """Initialize a MyGekko switch."""
        super().__init__(coordinator, load, "loads")
        self._load = load

    @property
    def is_on(self) -> bool | None:
        """Check wether the swich is on."""
        return (
            self._load.state == LoadState.ON_PERMANENT
            or self._load.state == LoadState.ON_IMPULSE
        )

    async def async_turn_off(self, **kwargs):
        """Turn off the switch."""
        await self.coordinator.async_write(self._load.set_state, LoadState.OFF)

    async def async_turn_on(self, **kwargs):
        """Turn on the switch."""
        await self.coordinator.async_write(self._load.set_state, LoadState.ON_PERMANENT)


class MyGekkoEMobilChargeSwitch(MyGekkoEntity, SwitchEntity):
    """mygekko e-mobility charging switch."""

    _attr_name = "Charging"

    def __init__(self, coordinator, emobil: EMobil):
        """Initialize the charging switch."""
        super().__init__(coordinator, emobil, "emobil", "_charge")
        self._emobil = emobil

    @property
    def is_on(self) -> bool | None:
        """Return whether the wallbox is charging."""
        state = self._emobil.charge_state
        return None if state is None else state == EMobilChargeState.ON

    async def async_turn_on(self, **kwargs):
        """Start charging."""
        await self.coordinator.async_write(self._emobil.start_charge)

    async def async_turn_off(self, **kwargs):
        """Stop charging."""
        await self.coordinator.async_write(self._emobil.stop_charge)
