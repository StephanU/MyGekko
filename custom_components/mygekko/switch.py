"""Switch platform for MyGekko."""
from homeassistant.components.switch import SwitchEntity
from homeassistant.core import callback
from PyMyGekko.resources.EMobils import EMobil
from PyMyGekko.resources.EMobils import EMobilChargeState
from PyMyGekko.resources.Loads import Load
from PyMyGekko.resources.Loads import LoadState

from .const import DOMAIN
from .entity import MyGekkoEntity


async def async_setup_entry(hass, entry, async_add_devices):
    """Set up switch platform."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    loads = coordinator.api.get_loads()
    if loads is not None:
        async_add_devices(MyGekkoSwitch(coordinator, load) for load in loads)

    async_add_devices(
        MyGekkoEMobilChargeSwitch(coordinator, emobil)
        for emobil in coordinator.api.get_emobils()
    )


class MyGekkoSwitch(MyGekkoEntity, SwitchEntity):
    """mygekko Switch class."""

    _attr_name = None

    def __init__(self, coordinator, load: Load):
        """Initialize a MyGekko switch."""
        super().__init__(coordinator, load, "loads")
        self._load = load

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        self.async_write_ha_state()

    @property
    def is_on(self) -> bool | None:
        """Check wether the swich is on."""
        state = self._get_optimistic("state", self._load.state)
        return state == LoadState.ON_PERMANENT or state == LoadState.ON_IMPULSE

    async def async_turn_off(self, **kwargs):
        """Turn off the switch."""
        await self._load.set_state(LoadState.OFF)
        self._set_optimistic("state", LoadState.OFF, self._load.state)
        await self.coordinator.async_request_refresh()

    async def async_turn_on(self, **kwargs):
        """Turn on the switch."""
        await self._load.set_state(LoadState.ON_PERMANENT)
        self._set_optimistic("state", LoadState.ON_PERMANENT, self._load.state)
        await self.coordinator.async_request_refresh()


class MyGekkoEMobilChargeSwitch(MyGekkoEntity, SwitchEntity):
    """mygekko charging station charge switch class."""

    _attr_translation_key = "mygekko_emobil_charge"
    _attr_icon = "mdi:ev-station"

    def __init__(self, coordinator, emobil: EMobil):
        """Initialize a MyGekko charging station charge switch."""
        super().__init__(coordinator, emobil, "emobils", "charge")
        self._emobil = emobil

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        self.async_write_ha_state()

    @property
    def is_on(self) -> bool | None:
        """Check whether the charging station is charging."""
        state = self._get_optimistic("state", self._emobil.charge_state)
        return state == EMobilChargeState.ON

    async def async_turn_off(self, **kwargs):
        """Stop charging."""
        await self._emobil.stop_charge()
        self._set_optimistic("state", EMobilChargeState.OFF, self._emobil.charge_state)
        await self.coordinator.async_request_refresh()

    async def async_turn_on(self, **kwargs):
        """Start charging."""
        await self._emobil.start_charge()
        self._set_optimistic("state", EMobilChargeState.ON, self._emobil.charge_state)
        await self.coordinator.async_request_refresh()
