"""Tests for the options of the integration."""
from homeassistant.data_entry_flow import FlowResultType


async def test_options_flow(hass, setup_demo):
    """The poll interval can be configured and is applied after the reload."""
    assert setup_demo.runtime_data.base_interval.total_seconds() == 30
    result = await hass.config_entries.options.async_init(setup_demo.entry_id)
    assert result["type"] is FlowResultType.FORM
    result = await hass.config_entries.options.async_configure(
        result["flow_id"], {"scan_interval": 90, "use_pages_as_areas": True}
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    await hass.async_block_till_done()
    assert setup_demo.options == {"scan_interval": 90, "use_pages_as_areas": True}
    assert setup_demo.runtime_data.base_interval.total_seconds() == 90
