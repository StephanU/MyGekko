"""Diagnostics support for MyGekko."""
from __future__ import annotations

from typing import Any

from homeassistant.components.diagnostics import async_redact_data
from homeassistant.const import CONF_API_KEY
from homeassistant.const import CONF_IP_ADDRESS
from homeassistant.const import CONF_PASSWORD
from homeassistant.const import CONF_USERNAME
from homeassistant.components.climate import ClimateEntity
from homeassistant.const import __version__ as HA_VERSION
from homeassistant.core import HomeAssistant

from .api.schema import SPECS
from .const import CONF_GEKKOID
from .const import VERSION
from .coordinator import MyGekkoConfigEntry

TO_REDACT = {CONF_API_KEY, CONF_GEKKOID, CONF_IP_ADDRESS, CONF_PASSWORD, CONF_USERNAME}


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: MyGekkoConfigEntry
) -> dict[str, Any]:
    """Return diagnostics for a config entry (no credentials, no device names)."""
    coordinator = entry.runtime_data
    store = coordinator.api.store
    return {
        "home_assistant": {
            "version": HA_VERSION,
            "integration_version": VERSION,
            # Home Assistant 2026.11 renamed the temperature API of climate entities
            "native_temperature_api": hasattr(ClimateEntity, "native_temperature_unit"),
        },
        "entry": {
            "version": entry.version,
            "data": async_redact_data(dict(entry.data), TO_REDACT),
        },
        "coordinator": {
            "last_update_success": coordinator.last_update_success,
            "update_interval": str(coordinator.update_interval),
            "api_state": coordinator.api_state,
            "backoff_active": coordinator.is_backing_off,
            "rate_limited_until": str(coordinator.rate_limited_until),
            "last_success": str(coordinator.last_success),
        },
        "controller": {
            key: value
            for key, value in store.globals_network.items()
            if key in ("version", "hardware")
        },
        "devices": {spec.kind: len(store.devices(spec)) for spec in SPECS},
    }
