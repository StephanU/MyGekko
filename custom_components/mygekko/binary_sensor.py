"""Binary sensor platform for MyGekko."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from homeassistant.components.binary_sensor import BinarySensorDeviceClass
from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.components.binary_sensor import BinarySensorEntityDescription

from .api import AccessDoorAccessState
from .api import AccessDoorAccessType
from .api import AlarmSystemAlarmState
from .api import AlarmSystemSharpState
from .api import AlarmSystemZoneAlarmState
from .api import EMobilChargeRequestState
from .api import EMobilPluggedState
from .api import EnergyManagerState
from .api import HeatingCircuitCoolingModeState
from .api import HeatingCircuitState
from .api import OnOffState
from .entity import MyGekkoEntity

PARALLEL_UPDATES = 0


@dataclass(frozen=True, kw_only=True)
class MyGekkoBinarySensorDescription(BinarySensorEntityDescription):
    """Describes a binary sensor that is on when `attr` of the device equals `on`."""

    attr: str
    on: Any


def _description(group, key, attr, on, name, device_class=None):
    return MyGekkoBinarySensorDescription(
        key=key,
        attr=attr,
        on=on,
        name=name,
        translation_key=f"mygekko_{group}_{key}",
        device_class=device_class,
    )


ACCESS_DOOR = (
    _description("accessdoor", "open", "access_state", AccessDoorAccessState.OPEN, "Open"),
)
EMOBIL = (
    _description(
        "emobil", "plugged", "plugged_state", EMobilPluggedState.PLUGGED, "Plugged in",
        BinarySensorDeviceClass.PLUG,
    ),
    _description(
        "emobil", "charge_request", "charge_request_state", EMobilChargeRequestState.ON,
        "Charge request",
    ),
)
ENERGY_MANAGER = (
    _description(
        "energymanager", "load_shedding", "load_shedding_state", EnergyManagerState.ON,
        "Load shedding",
    ),
    _description("energymanager", "ems", "ems_state", EnergyManagerState.ON, "Energy management active"),
)
HEATING_CIRCUIT = (
    _description(
        "heatingcircuit", "running", "state", HeatingCircuitState.ON, "Running",
        BinarySensorDeviceClass.RUNNING,
    ),
    _description(
        "heatingcircuit", "cooling", "cooling_mode_state",
        HeatingCircuitCoolingModeState.ON, "Cooling",
    ),
)
HEATING_SYSTEM = (
    _description(
        "heatingsystem", "running", "state", OnOffState.ON, "Running",
        BinarySensorDeviceClass.RUNNING,
    ),
    _description("heatingsystem", "cooling", "cooling_mode_state", OnOffState.ON, "Cooling"),
)
ALARM_SYSTEM = (
    _description(
        "alarmsystem", "alarm", "alarm_state", AlarmSystemAlarmState.ALARM, "Alarm",
        BinarySensorDeviceClass.SAFETY,
    ),
)
SMS_EMAIL = (_description("smsemail", "active", "state", OnOffState.ON, "Active"),)
MULTIROOM = (_description("multiroom", "playing", "player_state", OnOffState.ON, "Playing"),)


class MyGekkoBinarySensor(MyGekkoEntity, BinarySensorEntity):
    """Binary sensor reading one property of a MyGekko device."""

    entity_description: MyGekkoBinarySensorDescription

    def __init__(self, coordinator, device, prefix, description, placeholders=None):
        """Initialize the binary sensor."""
        super().__init__(coordinator, device, prefix, f"_{description.key}")
        self.entity_description = description
        self._device = device
        if placeholders:
            self._attr_translation_placeholders = placeholders

    @property
    def device_class(self) -> BinarySensorDeviceClass | None:
        """Return the device class, gates and barriers are no doors."""
        device = self._device
        if self.entity_description.key == "open" and device.access_type in (
            AccessDoorAccessType.GATE_CONTROL,
            AccessDoorAccessType.BARRIER_CONTROL,
            AccessDoorAccessType.GATE_OPERATION,
        ):
            return BinarySensorDeviceClass.OPENING
        if self.entity_description.key == "open":
            return BinarySensorDeviceClass.DOOR
        return self.entity_description.device_class

    @property
    def is_on(self) -> bool | None:
        """Return whether the property has the value that means on."""
        value = getattr(self._device, self.entity_description.attr, None)
        return None if value is None else value == self.entity_description.on


class MyGekkoAlarmZoneBinarySensor(MyGekkoBinarySensor):
    """Armed or alarm state of a zone of the alarm system."""

    def __init__(self, coordinator, device, zone, kind):
        """Initialize the zone binary sensor, `kind` is "armed" or "alarm"."""
        zone_name = getattr(device, f"zone{zone}_name") or f"{zone}"
        if kind == "armed":
            description = MyGekkoBinarySensorDescription(
                key=f"zone{zone}_armed",
                attr=f"zone{zone}_sharp_state",
                on=AlarmSystemSharpState.SHARP,
                name="Zone {zone} armed",
                translation_key="mygekko_alarmsystem_zone_armed",
            )
        else:
            description = MyGekkoBinarySensorDescription(
                key=f"zone{zone}_alarm",
                attr=f"zone{zone}_alarm_state",
                on=AlarmSystemZoneAlarmState.ALARM,
                name="Zone {zone} alarm",
                translation_key="mygekko_alarmsystem_zone_alarm",
                device_class=BinarySensorDeviceClass.SAFETY,
            )
        super().__init__(
            coordinator, device, "alarm_system", description, {"zone": zone_name}
        )

    @property
    def is_on(self) -> bool | None:
        """Return whether the zone is armed or in alarm."""
        value = getattr(self._device, self.entity_description.attr, None)
        if value is None:
            return None
        if self.entity_description.on == AlarmSystemZoneAlarmState.ALARM:
            # an alarm of a zone that is not armed counts as alarm as well
            return value != AlarmSystemZoneAlarmState.OK
        return value == self.entity_description.on


async def async_setup_entry(hass, entry, async_add_entities):
    """Set up the binary sensor platform."""
    coordinator = entry.runtime_data
    api = coordinator.api
    groups = (
        (api.get_access_doors(), "access_door", ACCESS_DOOR),
        (api.get_emobils(), "emobil", EMOBIL),
        (api.get_energy_managers(), "energy_manager", ENERGY_MANAGER),
        (api.get_heating_circuits(), "heating_circuit", HEATING_CIRCUIT),
        (api.get_heating_systems(), "heating_system", HEATING_SYSTEM),
        (api.get_alarm_systems(), "alarm_system", ALARM_SYSTEM),
        (api.get_sms_emails(), "sms_email", SMS_EMAIL),
        (api.get_multirooms(), "multiroom", MULTIROOM),
    )
    entities: list[BinarySensorEntity] = [
        MyGekkoBinarySensor(coordinator, device, prefix, description)
        for devices, prefix, descriptions in groups
        for device in devices
        for description in descriptions
    ]
    for alarm_system in api.get_alarm_systems():
        for zone in (1, 2):
            if getattr(alarm_system, f"zone{zone}_device_status") == OnOffState.ON:
                entities.append(MyGekkoAlarmZoneBinarySensor(coordinator, alarm_system, zone, "armed"))
                entities.append(MyGekkoAlarmZoneBinarySensor(coordinator, alarm_system, zone, "alarm"))
    async_add_entities(entities)
