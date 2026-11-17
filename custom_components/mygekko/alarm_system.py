"""Shared parts of the MyGekko alarm system entities.

myGEKKO mirrors an external intrusion alarm panel in its system "alarmsystem":
one item per security area ("Sicherungsbereich"). Every item also carries the
values of the whole panel (model, panel state, input group states), which are
identical in all items. The entities therefore get two kinds of devices: one
per security area and one for the panel, which reads the panel values from the
first item.
"""
import asyncio

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import callback
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from PyMyGekko.resources.AlarmSystems import AlarmSystem
from PyMyGekko.resources.AlarmSystems import AlarmSystemDeviceModel

from .const import CONF_SECURITY_AREA
from .const import DOMAIN
from .const import NAME
from .const import SUBENTRY_TYPE_INPUT_GROUP
from .entity import MyGekkoEntity
from .entity import scoped_id

ALARM_SYSTEM_ENTITY_PREFIX = "alarm_system"

# Learning an input group polls the controller itself, so it takes the same
# number of polls whatever update interval the entry uses.
LEARN_POLL_INTERVAL = 5
LEARN_BASELINE_POLLS = 6
LEARN_DETECT_POLLS = 12
LEARN_STABLE_POLLS = 2

# All device models myGEKKO reports are TELENOT panels.
_DEVICE_MODELS = {
    AlarmSystemDeviceModel.COMPLEX400_V2: ("TELENOT", "complex 400"),
    AlarmSystemDeviceModel.HIPLEX8400_V2: ("TELENOT", "hiplex 8400"),
}


def panel_device_id(coordinator) -> str:
    """Return the device identifier of the alarm panel."""
    return scoped_id(
        coordinator.config_entry.entry_id, f"{ALARM_SYSTEM_ENTITY_PREFIX}_panel"
    )


def security_area_device_id(coordinator, alarm_system: AlarmSystem) -> str:
    """Return the device identifier of a security area."""
    return scoped_id(
        coordinator.config_entry.entry_id,
        f"{ALARM_SYSTEM_ENTITY_PREFIX}{alarm_system.entity_id}",
    )


def input_group_device_id(coordinator, subentry_id: str) -> str:
    """Return the device identifier of an input group (one per subentry)."""
    return scoped_id(coordinator.config_entry.entry_id, subentry_id)


def panel_device_info(coordinator, alarm_system: AlarmSystem) -> DeviceInfo:
    """Return the device info of the alarm panel."""
    manufacturer, model = _DEVICE_MODELS.get(alarm_system.device_model, (None, None))
    return DeviceInfo(
        identifiers={(DOMAIN, panel_device_id(coordinator))},
        translation_key="alarm_panel",
        manufacturer=manufacturer,
        model=model,
    )


def get_alarm_systems(coordinator) -> list[AlarmSystem]:
    """Return the security areas of the controller, empty without alarm system."""
    return coordinator.api.get_alarm_systems()


@callback
def async_register_alarm_system_devices(
    hass: HomeAssistant, entry: ConfigEntry, coordinator
) -> None:
    """Register the devices of the alarm system and how they are connected.

    The panel, its security areas and the input groups (one device per
    subentry, as a device belongs to a single subentry) are registered before
    the platforms add their entities, which only reference them. That way the
    connections can be set by device id, also on versions of Home Assistant
    without via_device_id in DeviceInfo.
    """
    alarm_systems = get_alarm_systems(coordinator)
    if not alarm_systems:
        return

    device_registry = dr.async_get(hass)
    panel_info = panel_device_info(coordinator, alarm_systems[0])
    panel = device_registry.async_get_or_create(
        config_entry_id=entry.entry_id, **panel_info
    )

    area_device_ids = {}
    for alarm_system in alarm_systems:
        area = device_registry.async_get_or_create(
            config_entry_id=entry.entry_id,
            identifiers={(DOMAIN, security_area_device_id(coordinator, alarm_system))},
            manufacturer=NAME,
            name=alarm_system.name,
        )
        device_registry.async_update_device(area.id, via_device_id=panel.id)
        area_device_ids[alarm_system.entity_id] = area.id

    for subentry in entry.get_subentries_of_type(SUBENTRY_TYPE_INPUT_GROUP):
        device = device_registry.async_get_or_create(
            config_entry_id=entry.entry_id,
            config_subentry_id=subentry.subentry_id,
            identifiers={(DOMAIN, input_group_device_id(coordinator, subentry.subentry_id))},
            manufacturer=panel_info.get("manufacturer"),
            name=subentry.title,
        )
        # Connected through its security area if one is assigned.
        via_device_id = area_device_ids.get(
            subentry.data.get(CONF_SECURITY_AREA), panel.id
        )
        device_registry.async_update_device(device.id, via_device_id=via_device_id)


class MyGekkoSecurityAreaEntity(MyGekkoEntity):
    """Base class for the entities of a security area."""

    def __init__(self, coordinator, alarm_system: AlarmSystem, entity_suffix=""):
        """Initialize a security area entity."""
        super().__init__(
            coordinator, alarm_system, ALARM_SYSTEM_ENTITY_PREFIX, entity_suffix
        )
        self._alarm_system = alarm_system


class MyGekkoAlarmPanelEntity(CoordinatorEntity):
    """Base class for the entities of the alarm panel."""

    _attr_has_entity_name = True

    def __init__(self, coordinator, alarm_system: AlarmSystem, key: str):
        """Initialize an alarm panel entity from the first security area."""
        super().__init__(coordinator)
        self._alarm_system = alarm_system
        self._attr_unique_id = f"{panel_device_id(coordinator)}_{key}"
        self._attr_device_info = panel_device_info(coordinator, alarm_system)


def stable_new_input_groups(
    baseline: set[int], recent: list[set[int]], stable_polls: int
) -> set[int]:
    """Return the input groups active in each of the last polls but never before.

    Motion detectors switch every few seconds, so an input group only counts
    as triggered by the user when it was never active while recording the
    baseline and stays active for stable_polls polls in a row.
    """
    if len(recent) < stable_polls:
        return set()
    return set.intersection(*recent[-stable_polls:]) - baseline


class InputGroupLearner:
    """Find the index of the input group the user triggers, e.g. a window."""

    def __init__(self, coordinator) -> None:
        """Initialize the learner for the controller of the coordinator."""
        self._coordinator = coordinator
        self._baseline: set[int] = set()

    async def async_record_baseline(self) -> None:
        """Remember every input group active while nothing is triggered."""
        self._baseline = set()
        for poll in range(LEARN_BASELINE_POLLS):
            if poll:
                await asyncio.sleep(LEARN_POLL_INTERVAL)
            if (active := await self._async_poll()) is not None:
                self._baseline |= active

    async def async_detect(self) -> list[int]:
        """Return the candidates for the triggered input group, sorted.

        Ends as soon as exactly one candidate is stable, else after
        LEARN_DETECT_POLLS polls with whatever candidates are stable then.
        """
        recent: list[set[int]] = []
        candidates: set[int] = set()
        for poll in range(LEARN_DETECT_POLLS):
            if poll:
                await asyncio.sleep(LEARN_POLL_INTERVAL)
            if (active := await self._async_poll()) is None:
                continue
            recent.append(active)
            candidates = stable_new_input_groups(
                self._baseline, recent, LEARN_STABLE_POLLS
            )
            if len(candidates) == 1:
                break
        return sorted(candidates)

    async def _async_poll(self) -> set[int] | None:
        """Read the active input groups now, None if the poll failed."""
        await self._coordinator.async_refresh()
        if not self._coordinator.last_update_success:
            return None
        alarm_systems = get_alarm_systems(self._coordinator)
        if not alarm_systems:
            return None
        active = alarm_systems[0].active_input_groups
        return set(active) if active is not None else None
