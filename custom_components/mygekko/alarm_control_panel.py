"""Alarm control panel platform for MyGekko: shows the zones of the alarm system.

The alarm system cannot be armed or disarmed from Home Assistant. This is a deliberate
decision for a security relevant function, the panels only report the state.
"""
from homeassistant.components.alarm_control_panel import AlarmControlPanelEntity
from homeassistant.components.alarm_control_panel import AlarmControlPanelEntityFeature
from homeassistant.components.alarm_control_panel import AlarmControlPanelState
from homeassistant.exceptions import HomeAssistantError

from .api import AlarmSystem
from .api import AlarmSystemSharpState
from .api import AlarmSystemZoneAlarmState
from .api import OnOffState
from .const import DOMAIN
from .entity import MyGekkoEntity

PARALLEL_UPDATES = 0


async def async_setup_entry(hass, entry, async_add_entities):
    """Set up one panel for every zone in use."""
    coordinator = entry.runtime_data
    async_add_entities(
        MyGekkoAlarmZonePanel(coordinator, alarm_system, zone)
        for alarm_system in coordinator.api.get_alarm_systems()
        for zone in (1, 2)
        if getattr(alarm_system, f"zone{zone}_device_status") == OnOffState.ON
    )


class MyGekkoAlarmZonePanel(MyGekkoEntity, AlarmControlPanelEntity):
    """State of a zone of the alarm system (read only)."""

    _attr_supported_features = AlarmControlPanelEntityFeature(0)
    _attr_code_arm_required = False
    _attr_translation_key = "mygekko_alarmsystem_zone"

    def __init__(self, coordinator, alarm_system: AlarmSystem, zone: int):
        """Initialize the panel of a zone."""
        super().__init__(coordinator, alarm_system, "alarm_system", f"_zone{zone}_panel")
        self._alarm_system = alarm_system
        self._zone = zone
        self._attr_translation_placeholders = {
            "zone": getattr(alarm_system, f"zone{zone}_name") or str(zone)
        }

    @property
    def alarm_state(self) -> AlarmControlPanelState | None:
        """Return triggered, armed or disarmed."""
        alarm = getattr(self._alarm_system, f"zone{self._zone}_alarm_state")
        sharp = getattr(self._alarm_system, f"zone{self._zone}_sharp_state")
        if alarm is None and sharp is None:
            return None
        # an alarm of a zone that is not armed (unsharp) does not trigger the panel
        if sharp == AlarmSystemSharpState.SHARP and alarm not in (
            None,
            AlarmSystemZoneAlarmState.OK,
        ):
            return AlarmControlPanelState.TRIGGERED
        if alarm == AlarmSystemZoneAlarmState.ALARM:
            return AlarmControlPanelState.TRIGGERED
        if sharp == AlarmSystemSharpState.SHARP:
            return AlarmControlPanelState.ARMED_AWAY
        return AlarmControlPanelState.DISARMED

    async def async_alarm_disarm(self, code: str | None = None) -> None:
        """Disarming is not possible from Home Assistant."""
        raise HomeAssistantError(
            translation_domain=DOMAIN, translation_key="alarm_read_only"
        )
