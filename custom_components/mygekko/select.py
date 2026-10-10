"""Select platform for MyGekko."""
from homeassistant.components.select import SelectEntity
from homeassistant.components.select import SelectEntityDescription
from .api import Clock
from .api import ClockState
from .api import Vent
from .api import VentBypassMode
from .api import VentWorkingLevel
from .api import VentWorkingMode

from .entity import MyGekkoEntity


async def async_setup_entry(hass, entry, async_add_devices):
    """Set up select platform."""
    coordinator = entry.runtime_data

    async_add_devices(
        MyGekkoClockSelect(coordinator, clock)
        for clock in coordinator.api.get_clocks() or []
    )
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
        return (
            str(self._vent.bypass_state)
            if self._vent.bypass_state is not None
            else None
        )

    async def async_select_option(self, option: str) -> None:
        """Change the selected option."""
        await self.coordinator.async_write(self._vent.set_bypass_state, option)


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
        return (
            str(self._vent.working_mode)
            if self._vent.working_mode is not None
            else None
        )

    async def async_select_option(self, option: str) -> None:
        """Change the selected option."""
        await self.coordinator.async_write(self._vent.set_working_mode, option)


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
        return (
            str(self._vent.working_level)
            if self._vent.working_level is not None
            else None
        )

    async def async_select_option(self, option: str) -> None:
        """Change the selected option."""
        await self.coordinator.async_write(self._vent.set_working_level, VentWorkingLevel(int(option)))


class MyGekkoClockSelect(MyGekkoEntity, SelectEntity):
    """mygekko clock (time switch) mode select."""

    _attr_name = None
    _attr_options = [state.name.lower() for state in ClockState]

    def __init__(self, coordinator, clock: Clock):
        """Initialize a MyGekko clock select."""
        super().__init__(coordinator, clock, "clocks")
        self._clock = clock

    @property
    def current_option(self) -> str | None:
        """Return the current clock mode."""
        state = self._clock.state
        return state.name.lower() if state is not None else None

    async def async_select_option(self, option: str) -> None:
        """Change the clock mode."""
        await self.coordinator.async_write(
            self._clock.set_state, ClockState[option.upper()]
        )
