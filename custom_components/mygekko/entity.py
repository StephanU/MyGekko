"""MyGekkoEntity class."""
import logging
import time
from typing import Any

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from PyMyGekko.resources import ReadOnlyEntity

from .const import DOMAIN
from .const import MANUFACTURER
from .const import NAME

_LOGGER: logging.Logger = logging.getLogger(__name__)

# How long (in seconds) an optimistic value is shown before falling back to
# the polled value. Long enough to bridge a stale poll right after a command,
# short enough to recover from commands the myGekko never applied.
OPTIMISTIC_VALUE_TIMEOUT = 60.0


def scoped_id(entry_id: str, resource_id: str) -> str:
    """Scope a MyGekko resource id to a config entry.

    The ids reported by a MyGekko controller (e.g. "lightsitem13") are only unique
    within that controller, so they have to be namespaced to keep multiple
    controllers from clashing in the entity and device registry.
    """
    return f"{entry_id}_{resource_id}"


class MyGekkoEntity(CoordinatorEntity):
    """Base Class for MyGekko entities."""

    _attr_has_entity_name = True

    def __init__(
        self, coordinator, entity: ReadOnlyEntity, entity_prefix: str, entity_suffix: str = ""
    ):
        """Initialize a MyGekko entity."""
        super().__init__(coordinator)

        self._optimistic_values: dict[str, tuple[Any, Any, float]] = {}

        device_id = scoped_id(
            coordinator.config_entry.entry_id, f"{entity_prefix}{entity.entity_id}"
        )
        device_name = entity.name

        self._attr_unique_id = f"{device_id}{entity_suffix}"

        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, device_id)},
            manufacturer=NAME,
            name=device_name,
        )

        _LOGGER.debug("Added MyGekko entity id='%s'", self.unique_id)

    def _set_optimistic(self, key: str, optimistic_value, polled_value) -> None:
        """Show a value immediately instead of waiting for the next poll.

        The optimistic value is returned by _get_optimistic until the polled
        value changes (the myGekko has processed the command) or the timeout
        expires (the command got lost), so a stale poll right after a command
        does not flip the state back.
        """
        self._optimistic_values[key] = (
            optimistic_value,
            polled_value,
            time.monotonic() + OPTIMISTIC_VALUE_TIMEOUT,
        )
        self.async_write_ha_state()

    def _get_optimistic(self, key: str, polled_value):
        """Return the optimistic value for key while it is valid."""
        if key not in self._optimistic_values:
            return polled_value
        optimistic_value, initial_value, valid_until = self._optimistic_values[key]
        if polled_value != initial_value or time.monotonic() >= valid_until:
            del self._optimistic_values[key]
            return polled_value
        return optimistic_value


class MyGekkoControllerEntity(CoordinatorEntity):
    """Base Class for MyGekko controller entities."""

    _attr_has_entity_name = True

    def __init__(
        self, coordinator, entity: ReadOnlyEntity, globals_network, entity_prefix: str
    ):
        """Initialize a MyGekko controller entity."""
        super().__init__(coordinator)

        device_id = scoped_id(
            coordinator.config_entry.entry_id,
            f"mygekko_controller_{globals_network['gekkoname']}",
        )
        device_name = globals_network["gekkoname"]

        self._attr_unique_id = f"{device_id}{entity_prefix}{entity.entity_id}"
        self._attr_name = f"{entity.name}"

        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, device_id)},
            name=device_name,
            manufacturer=MANUFACTURER,
            sw_version=globals_network.get("version", "unknown"),
            hw_version=globals_network.get("hardware", "unknown"),
            model=globals_network.get("hardware", "unknown"),
        )

        _LOGGER.debug(
            "Added MyGekko controller entity: id='%s' name='%s'",
            self.unique_id,
            self.name,
        )
