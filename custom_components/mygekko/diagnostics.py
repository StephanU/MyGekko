"""Diagnostics support for MyGekko."""
from __future__ import annotations

from typing import Any

from homeassistant.components.diagnostics import async_redact_data
from homeassistant.const import CONF_API_KEY
from homeassistant.const import CONF_IP_ADDRESS
from homeassistant.const import CONF_PASSWORD
from homeassistant.const import CONF_USERNAME
from homeassistant.core import HomeAssistant

from .api.schema import SPECS
from .const import CONF_GEKKOID
from .coordinator import MyGekkoConfigEntry

TO_REDACT = {CONF_API_KEY, CONF_GEKKOID, CONF_IP_ADDRESS, CONF_PASSWORD, CONF_USERNAME}


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: MyGekkoConfigEntry
) -> dict[str, Any]:
    """Return diagnostics for a config entry (no credentials, no device names)."""
    coordinator = entry.runtime_data
    store = coordinator.api.store
    return {
        "entry": {
            "version": entry.version,
            "data": async_redact_data(dict(entry.data), TO_REDACT),
        },
        "coordinator": {
            "last_update_success": coordinator.last_update_success,
            "update_interval": str(coordinator.update_interval),
            "skipped_polls": coordinator._skipped_polls,
            "backoff_active": coordinator.is_backing_off,
        },
        "controller": {
            key: value
            for key, value in store.globals_network.items()
            if key in ("version", "hardware")
        },
        "devices": {spec.kind: len(store.devices(spec)) for spec in SPECS},
    }
