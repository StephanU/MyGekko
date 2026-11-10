"""MyGekkoEntity class."""
import asyncio
import logging
import time
from dataclasses import dataclass
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


@dataclass
class OptimisticValue:
    """A value shown before a poll reports it."""

    value: Any
    # Polled values that do not show the latest command yet, oldest first: the
    # one polled when the first pending command was sent, then the values of
    # the commands sent after it except the latest.
    unconfirmed: list[Any]
    valid_until: float


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

        self._optimistic_values: dict[str, OptimisticValue] = {}
        # Held while a command is sent and its optimistic value is set.
        # Service calls run concurrently, so without it a later command could
        # reach the myGekko first, or be recorded before an earlier one.
        self._command_lock = asyncio.Lock()

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

        The optimistic value is returned by _get_optimistic until a poll shows
        a value no pending command has caused (the myGekko has processed the
        latest command, or the value was changed elsewhere) or the timeout
        expires (the command got lost), so a stale poll right after a command
        does not flip the state back.

        Each command triggers a poll. If the next command is sent while that
        poll is still running, the poll returns the value of the earlier
        command. Such a value does not end the optimistic value either.
        """
        pending = self._pending_optimistic(key, polled_value)
        self._optimistic_values[key] = OptimisticValue(
            optimistic_value,
            [polled_value]
            if pending is None
            else [*pending.unconfirmed, pending.value],
            time.monotonic() + OPTIMISTIC_VALUE_TIMEOUT,
        )
        self.async_write_ha_state()

    def _clear_optimistic(self, key: str) -> None:
        """Drop the optimistic value of commands a newer one has superseded."""
        if self._optimistic_values.pop(key, None) is not None:
            self.async_write_ha_state()

    def _get_optimistic(self, key: str, polled_value, reference=None):
        """Return the optimistic value for key while it is valid.

        By default polled_value is compared with the value passed to
        _set_optimistic. A value that returns to its initial state on its own
        (a blind that stops after a short movement) passes a reference that
        holds more than that value, and _set_optimistic gets the same kind.
        The values of earlier commands are not of that kind, so there only the
        reference polled when the first pending command was sent counts.
        """
        pending = self._pending_optimistic(
            key, polled_value if reference is None else reference
        )
        return polled_value if pending is None else pending.value

    def _pending_optimistic(self, key: str, reference) -> OptimisticValue | None:
        """Return the optimistic value for key, or drop it once it is outdated."""
        pending = self._optimistic_values.get(key)
        if pending is None:
            return None
        if time.monotonic() < pending.valid_until and reference in pending.unconfirmed:
            # The commands before the one the poll shows have been processed.
            del pending.unconfirmed[: pending.unconfirmed.index(reference)]
            return pending
        del self._optimistic_values[key]
        return None


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
