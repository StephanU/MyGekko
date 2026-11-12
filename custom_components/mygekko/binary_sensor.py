"""Binary sensor platform for MyGekko.

Input groups ("Meldebereiche") of the alarm panel: myGEKKO reports which input
groups are active, but neither their names nor their kind. Each input group the
user adds as config subentry (index, name, device class, security area) becomes
one binary sensor.
"""
from homeassistant.components.binary_sensor import BinarySensorDeviceClass
from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.config_entries import ConfigSubentry
from homeassistant.const import CONF_DEVICE_CLASS
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from PyMyGekko.resources.AlarmSystems import AlarmSystem

from .alarm_system import get_alarm_systems
from .alarm_system import input_group_device_id
from .const import CONF_INPUT_GROUP_INDEX
from .const import DOMAIN
from .const import SUBENTRY_TYPE_INPUT_GROUP


async def async_setup_entry(hass, entry, async_add_entities):
    """Set up the binary sensor platform."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    alarm_systems = get_alarm_systems(coordinator)
    if not alarm_systems:
        return

    for subentry in entry.get_subentries_of_type(SUBENTRY_TYPE_INPUT_GROUP):
        async_add_entities(
            [MyGekkoInputGroupBinarySensor(coordinator, alarm_systems, subentry)],
            config_subentry_id=subentry.subentry_id,
        )


class MyGekkoInputGroupBinarySensor(CoordinatorEntity, BinarySensorEntity):
    """An input group of the alarm panel, on while it is active (e.g. open)."""

    _attr_has_entity_name = True
    _attr_name = None

    def __init__(
        self,
        coordinator,
        alarm_systems: list[AlarmSystem],
        subentry: ConfigSubentry,
    ):
        """Initialize an input group binary sensor."""
        super().__init__(coordinator)
        # Any security area reports the input groups of the whole panel.
        self._alarm_system = alarm_systems[0]
        self._index = subentry.data[CONF_INPUT_GROUP_INDEX]

        device_id = input_group_device_id(coordinator, subentry.subentry_id)
        self._attr_unique_id = device_id
        self._attr_device_info = DeviceInfo(identifiers={(DOMAIN, device_id)})
        if device_class := subentry.data.get(CONF_DEVICE_CLASS):
            self._attr_device_class = BinarySensorDeviceClass(device_class)
        self._attr_extra_state_attributes = {"input_group_index": self._index}

    @property
    def available(self) -> bool:
        """Return if the input group is reported."""
        count = self._alarm_system.input_group_count
        return super().available and count is not None and self._index < count

    @property
    def is_on(self) -> bool | None:
        """Return whether the input group is active."""
        active = self._alarm_system.active_input_groups
        return self._index in active if active is not None else None
