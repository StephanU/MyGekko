"""Alarm control panel platform for MyGekko: one panel per security area."""
from homeassistant.components.alarm_control_panel import AlarmControlPanelEntity
from homeassistant.components.alarm_control_panel import (
    AlarmControlPanelEntityFeature,
)
from homeassistant.components.alarm_control_panel import AlarmControlPanelState
from homeassistant.exceptions import ServiceValidationError
from PyMyGekko.resources.AlarmSystems import AlarmSystem
from PyMyGekko.resources.AlarmSystems import AlarmSystemAlarmState
from PyMyGekko.resources.AlarmSystems import AlarmSystemFeature
from PyMyGekko.resources.AlarmSystems import AlarmSystemSharpState

from .alarm_system import get_alarm_systems
from .alarm_system import MyGekkoSecurityAreaEntity
from .const import CONF_ALARM_SYSTEM_READ_ONLY
from .const import DOMAIN

# Shown while an arming command has not reached the panel state yet.
_ARMING = "arming"

_STATE_BY_SHARP_STATE = {
    AlarmSystemSharpState.UNSHARP: AlarmControlPanelState.DISARMED,
    AlarmSystemSharpState.INTERNAL_SHARP: AlarmControlPanelState.ARMED_HOME,
    AlarmSystemSharpState.EXTERNAL_SHARP: AlarmControlPanelState.ARMED_AWAY,
}

_ENTITY_FEATURE_BY_FEATURE = {
    AlarmSystemFeature.ARM_INTERNAL: AlarmControlPanelEntityFeature.ARM_HOME,
    AlarmSystemFeature.ARM_EXTERNAL: AlarmControlPanelEntityFeature.ARM_AWAY,
}


async def async_setup_entry(hass, entry, async_add_entities):
    """Set up the alarm control panel platform."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    read_only = entry.options.get(CONF_ALARM_SYSTEM_READ_ONLY, False)
    async_add_entities(
        MyGekkoAlarmControlPanel(coordinator, alarm_system, read_only)
        for alarm_system in get_alarm_systems(coordinator)
    )


class MyGekkoAlarmControlPanel(MyGekkoSecurityAreaEntity, AlarmControlPanelEntity):
    """The arming state of one security area of the alarm panel.

    myGEKKO only accepts the commands its scmd format announces. For TELENOT
    panels these are internal and external arming: disarming needs the
    password set in myGEKKO and is not offered by the Query API. A code entered
    in Home Assistant could not be passed on, so none is asked for.
    """

    _attr_name = None
    _attr_code_arm_required = False
    _attr_code_format = None

    def __init__(self, coordinator, alarm_system: AlarmSystem, read_only: bool):
        """Initialize the alarm control panel of a security area."""
        super().__init__(coordinator, alarm_system)
        self._read_only = read_only

        features = AlarmControlPanelEntityFeature(0)
        if not read_only:
            for feature in alarm_system.supported_features:
                features |= _ENTITY_FEATURE_BY_FEATURE.get(
                    feature, AlarmControlPanelEntityFeature(0)
                )
        self._attr_supported_features = features

    @property
    def alarm_state(self) -> AlarmControlPanelState | None:
        """Return the state of the security area."""
        if self._alarm_system.alarm_state == AlarmSystemAlarmState.ALARM:
            return AlarmControlPanelState.TRIGGERED

        sharp_state = self._get_optimistic(
            "sharp_state", self._alarm_system.sharp_state
        )
        if sharp_state == _ARMING:
            return AlarmControlPanelState.ARMING
        return _STATE_BY_SHARP_STATE.get(sharp_state)

    async def async_alarm_arm_home(self, code: str | None = None) -> None:
        """Arm the security area internally."""
        await self._async_set_sharp_state(
            AlarmSystemFeature.ARM_INTERNAL, AlarmSystemSharpState.INTERNAL_SHARP
        )

    async def async_alarm_arm_away(self, code: str | None = None) -> None:
        """Arm the security area externally."""
        await self._async_set_sharp_state(
            AlarmSystemFeature.ARM_EXTERNAL, AlarmSystemSharpState.EXTERNAL_SHARP
        )

    async def async_alarm_disarm(self, code: str | None = None) -> None:
        """Disarm the security area, which the myGEKKO Query API does not offer."""
        await self._async_set_sharp_state(
            AlarmSystemFeature.DISARM, AlarmSystemSharpState.UNSHARP
        )

    async def _async_set_sharp_state(
        self, feature: AlarmSystemFeature, state: AlarmSystemSharpState
    ) -> None:
        """Send an arming command, if this security area may receive it."""
        if self._read_only:
            raise ServiceValidationError(
                translation_domain=DOMAIN,
                translation_key="alarm_system_read_only",
                translation_placeholders={"name": self._alarm_system.name},
            )
        if feature not in self._alarm_system.supported_features:
            raise ServiceValidationError(
                translation_domain=DOMAIN,
                translation_key="alarm_system_command_not_supported",
                translation_placeholders={"name": self._alarm_system.name},
            )

        async with self._command_lock:
            await self._alarm_system.set_sharp_state(state)
            if state != AlarmSystemSharpState.UNSHARP:
                # The panel only reports the new state once its exit delay has
                # passed, or never if an open input group prevents arming.
                self._set_optimistic(
                    "sharp_state", _ARMING, self._alarm_system.sharp_state
                )
        await self.coordinator.async_request_refresh()

