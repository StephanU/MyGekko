"""Select platform for MyGekko."""
from homeassistant.components.select import SelectEntity
from homeassistant.components.select import SelectEntityDescription
from PyMyGekko.resources.Vents import Vent
from PyMyGekko.resources.Vents import VentBypassMode
from PyMyGekko.resources.Vents import VentWorkingLevel
from PyMyGekko.resources.Vents import VentWorkingMode

from .const import DOMAIN
from .entity import MyGekkoEntity


async def async_setup_entry(hass, entry, async_add_devices):
    """Set up select platform."""
    coordinator = hass.data[DOMAIN][entry.entry_id]

    async_add_devices(
        MyGekkoVentBypassSelect(coordinator, vent)
        for vent in coordinator.api.get_vents()
    )
    async_add_devices(
        MyGekkoVentWorkingModeSelect(coordinator, vent)
        for vent in coordinator.api.get_vents()
    )
    async_add_devices(
        MyGekkoVentWorkingLevelSelect(coordinator, vent)
        for vent in coordinator.api.get_vents()
    )


class MyGekkoVentBypassSelect(MyGekkoEntity, SelectEntity):
    """mygekko vent bypass select class."""

    def __init__(self, coordinator, vent: Vent):
        """Initialize a MyGekko vent bypass selection."""
        super().__init__(coordinator, vent, "vents", "Bypass")
        self._vent = vent
        self.entity_description = SelectEntityDescription(
            key="mygekko_vent_bypass",
            translation_key="mygekko_vent_bypass",
            options=[
                str(VentBypassMode.AUTO),
                str(VentBypassMode.SUMMER),
                str(VentBypassMode.MANUAL),
            ],
        )

    @property
    def current_option(self) -> str | None:
        """Return the selected entity option to represent the entity state."""
        bypass_state = self._get_optimistic("bypass_state", self._vent.bypass_state)
        return str(bypass_state) if bypass_state is not None else None

    async def async_select_option(self, option: str) -> None:
        """Change the selected option."""
        await self._vent.set_bypass_state(option)
        self._set_optimistic("bypass_state", option, self._vent.bypass_state)
        await self.coordinator.async_request_refresh()


class MyGekkoVentWorkingModeSelect(MyGekkoEntity, SelectEntity):
    """mygekko vent working mode select class."""

    def __init__(self, coordinator, vent: Vent):
        """Initialize a MyGekko vent working mode selection."""
        super().__init__(coordinator, vent, "vents", "Working Mode")
        self._vent = vent
        self.entity_description = SelectEntityDescription(
            key="mygekko_vent_working_mode",
            translation_key="mygekko_vent_working_mode",
            options=[
                str(VentWorkingMode.AUTO),
                str(VentWorkingMode.MANUAL),
                str(VentWorkingMode.PLUGGIT_AUTO),
                str(VentWorkingMode.PLUGGIT_WEEK),
            ],
        )

    @property
    def current_option(self) -> str | None:
        """Return the selected entity option to represent the entity state."""
        working_mode = self._get_optimistic("working_mode", self._vent.working_mode)
        return str(working_mode) if working_mode is not None else None

    async def async_select_option(self, option: str) -> None:
        """Change the selected option."""
        await self._vent.set_working_mode(option)
        self._set_optimistic("working_mode", option, self._vent.working_mode)
        await self.coordinator.async_request_refresh()


class MyGekkoVentWorkingLevelSelect(MyGekkoEntity, SelectEntity):
    """mygekko vent level select class."""

    def __init__(self, coordinator, vent: Vent):
        """Initialize a MyGekko vent working level selection."""
        super().__init__(coordinator, vent, "vents", "Level")
        self._vent = vent
        self.entity_description = SelectEntityDescription(
            key="mygekko_vent_working_level",
            translation_key="mygekko_vent_working_level",
            options=[
                str(VentWorkingLevel.LEVEL_1),
                str(VentWorkingLevel.LEVEL_2),
                str(VentWorkingLevel.LEVEL_3),
                str(VentWorkingLevel.LEVEL_4),
                str(VentWorkingLevel.OFF),
            ],
        )

    @property
    def current_option(self) -> str | None:
        """Return the selected entity option to represent the entity state."""
        working_level = self._get_optimistic("working_level", self._vent.working_level)
        return str(working_level) if working_level is not None else None

    async def async_select_option(self, option: str) -> None:
        """Change the selected option."""
        await self._vent.set_working_level(option)
        self._set_optimistic("working_level", option, self._vent.working_level)
        await self.coordinator.async_request_refresh()
