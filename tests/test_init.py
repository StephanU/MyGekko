"""Tests for setting up, unloading and migrating the integration."""
from unittest.mock import patch

from homeassistant.config_entries import ConfigEntryState
from homeassistant.const import EntityCategory
import json

from homeassistant.helpers import area_registry as ar
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers import issue_registry as ir
from homeassistant.helpers import entity_registry as er
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.mygekko.api import MyGekkoForbidden
from custom_components.mygekko.api import MyGekkoTooManyRequests
from custom_components.mygekko.const import CONF_CONNECTION_MY_GEKKO_CLOUD
from custom_components.mygekko.const import DOMAIN

from .const import CLOUD_CONFIG
from .const import CLOUD_INPUT
from .const import DEMO_CONFIG
from .const import LOCAL_CONFIG


def _demo(name):
    with open(f"custom_components/mygekko/api/demo/{name}", encoding="utf-8") as file:
        return json.load(file)


async def test_demo_setup_creates_entities(hass, setup_demo):
    """All platforms create their entities in demo mode."""
    domains = {state.domain for state in hass.states.async_all()}
    assert {
        "light",
        "cover",
        "climate",
        "switch",
        "sensor",
        "select",
        "scene",
        "button",
        "water_heater",
    } <= domains
    registry = er.async_get(hass)
    entries = er.async_entries_for_config_entry(registry, setup_demo.entry_id)
    assert len(entries) == len({entry.unique_id for entry in entries})
    assert dr.async_entries_for_config_entry(dr.async_get(hass), setup_demo.entry_id)


async def test_unload_and_reload(hass, setup_demo):
    """The entry can be unloaded and reloaded without leftovers."""
    count = len(hass.states.async_all())
    await hass.config_entries.async_reload(setup_demo.entry_id)
    await hass.async_block_till_done()
    assert setup_demo.state is ConfigEntryState.LOADED
    assert len(hass.states.async_all()) == count

    await hass.config_entries.async_unload(setup_demo.entry_id)
    await hass.async_block_till_done()
    assert setup_demo.state is ConfigEntryState.NOT_LOADED


async def test_setup_retries_when_gekko_is_not_reachable(hass):
    """An unreachable MyGekko makes the setup retry instead of fail."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        version=3,
        data={"connection_type": CONF_CONNECTION_MY_GEKKO_CLOUD, **CLOUD_INPUT},
    )
    entry.add_to_hass(hass)
    for error in (MyGekkoTooManyRequests("429"), TimeoutError()):
        with patch(
            "custom_components.mygekko.api.MyGekkoClient.read_data", side_effect=error
        ):
            await hass.config_entries.async_setup(entry.entry_id)
        assert entry.state is ConfigEntryState.SETUP_RETRY
        await hass.config_entries.async_unload(entry.entry_id)


async def test_migration_from_version_1(hass):
    """Old entries are migrated to the current version."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        version=1,
        data={"username": "u", "apikey": "k", "gekkoid": "g"},
    )
    entry.add_to_hass(hass)
    with patch("custom_components.mygekko.api.MyGekkoClient.read_data"):
        await hass.config_entries.async_setup(entry.entry_id)
    assert entry.version == 3
    assert entry.data["api_key"] == "k"
    assert "apikey" not in entry.data


async def test_rejected_credentials_start_reauth(hass):
    """A rejected login asks the user for new credentials."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        version=3,
        data={"connection_type": CONF_CONNECTION_MY_GEKKO_CLOUD, **CLOUD_INPUT},
    )
    entry.add_to_hass(hass)
    with patch(
        "custom_components.mygekko.api.MyGekkoClient.read_data",
        side_effect=MyGekkoForbidden("403"),
    ):
        await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()
    assert entry.state is ConfigEntryState.SETUP_ERROR
    flows = hass.config_entries.flow.async_progress_by_handler(DOMAIN)
    assert [flow["context"]["source"] for flow in flows] == ["reauth"]


async def test_controller_device(hass, setup_demo):
    """The controller is a device with model and version, devices connect to it."""
    registry = dr.async_get(hass)
    controller = registry.async_get_device_by_identifier(
        (DOMAIN, "mygekko_controller_myGEKKO Demo"), setup_demo.entry_id
    )
    assert controller is not None
    assert controller.sw_version
    assert controller.model

    light = registry.async_get_device_by_identifier(
        (DOMAIN, "lightsitem0"), setup_demo.entry_id
    )
    assert light is not None
    assert light.via_device_id == controller.id
    assert light.model == "Light"


async def test_noisy_sensors_are_disabled_by_default(hass, setup_demo):
    """The energy time frame sensors are off by default, power limits are diagnostic."""
    registry = er.async_get(hass)
    bucket = registry.async_get(
        "sensor.main_electricity_meter_total_energy_today_from_00_00_to_06_00"
    )
    assert bucket.disabled_by is er.RegistryEntryDisabler.INTEGRATION
    nominal = registry.async_get("sensor.main_electricity_meter_nominal_power")
    assert nominal.entity_category is EntityCategory.DIAGNOSTIC
    # the main values stay enabled
    assert registry.async_get("sensor.main_electricity_meter_total_energy").disabled_by is None


async def test_controller_keeps_its_configuration_url(hass):
    """The link to the web interface survives the creation of the controller entities."""
    entry = MockConfigEntry(
        domain=DOMAIN, version=3, data=LOCAL_CONFIG, unique_id="local_192.168.1.50"
    )
    entry.add_to_hass(hass)
    with patch(
        "custom_components.mygekko.api.MyGekkoHttpClient._fetch_resources",
        return_value=_demo("api_var_demo_data.json"),
    ), patch(
        "custom_components.mygekko.api.MyGekkoHttpClient._fetch_status",
        return_value=_demo("api_var_status_demo_data.json"),
    ):
        await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()
    controller = dr.async_get(hass).async_get_device_by_identifier(
        (DOMAIN, "mygekko_controller_myGEKKO Demo"), entry.entry_id
    )
    assert controller.configuration_url == "https://192.168.1.50"
    assert controller.sw_version


async def test_devices_use_via_device_id(hass, setup_demo, caplog):
    """The deprecated via_device is not used."""
    assert "via_device" not in caplog.text


async def test_pages_become_areas_on_request(hass):
    """The pages of MyGekko are suggested as areas when the option is on."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        version=3,
        data=DEMO_CONFIG,
        options={"use_pages_as_areas": True},
        unique_id="areas",
    )
    entry.add_to_hass(hass)
    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    names = {area.name for area in ar.async_get(hass).async_list_areas()}
    assert {"Entrance", "Technical room"} <= names


async def test_removing_the_entry_clears_the_repair_issue(hass, setup_demo):
    """A repair issue does not outlive its config entry."""
    issue_id = f"rate_limited_{setup_demo.entry_id}"
    ir.async_create_issue(
        hass, DOMAIN, issue_id, is_fixable=False,
        severity=ir.IssueSeverity.WARNING, translation_key="rate_limited",
    )
    await hass.config_entries.async_remove(setup_demo.entry_id)
    assert ir.async_get(hass).async_get_issue(DOMAIN, issue_id) is None


async def test_duplicate_entries_are_reported(hass):
    """The same MyGekko set up twice (one entry disabled) is reported and adopts its id."""
    from homeassistant.config_entries import ConfigEntryDisabler

    old = MockConfigEntry(
        domain=DOMAIN,
        version=3,
        data=CLOUD_CONFIG,
        unique_id=None,
        disabled_by=ConfigEntryDisabler.USER,
    )
    old.add_to_hass(hass)
    entry = MockConfigEntry(domain=DOMAIN, version=3, data=CLOUD_CONFIG, unique_id=None)
    entry.add_to_hass(hass)
    with patch(
        "custom_components.mygekko.api.MyGekkoHttpClient._fetch_resources",
        return_value=_demo("api_var_demo_data.json"),
    ), patch(
        "custom_components.mygekko.api.MyGekkoHttpClient._fetch_status",
        return_value=_demo("api_var_status_demo_data.json"),
    ):
        await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

    assert entry.unique_id == "cloud_A1B2C3"
    registry = ir.async_get(hass)
    issue = registry.async_get_issue(DOMAIN, f"duplicate_entry_{old.entry_id}")
    assert issue is not None
    assert issue.translation_placeholders["count"] == "2"
    assert issue.translation_placeholders["disabled"] == "1"

    await hass.config_entries.async_remove(old.entry_id)
    await hass.async_block_till_done()
    assert not [
        issue_id for (domain, issue_id) in registry.issues if domain == DOMAIN
        and issue_id.startswith("duplicate_entry")
    ]
