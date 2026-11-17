"""Test MyGekko sensors."""
from datetime import datetime
from unittest.mock import patch
from unittest.mock import PropertyMock

import pytest
from custom_components.mygekko import sensor
from custom_components.mygekko.const import CONF_DATE_ORDER
from custom_components.mygekko.const import DATE_ORDER_DAY_FIRST
from custom_components.mygekko.const import DATE_ORDER_MONTH_FIRST
from custom_components.mygekko.const import DOMAIN
from homeassistant.helpers import entity_registry as er
from homeassistant.util import dt as dt_util
from PyMyGekko.resources.EMobils import EMobil
from pytest_homeassistant_custom_component.common import MockConfigEntry

from .const import MOCK_DEMO_ENTRY_DATA

BOTH_DATE_ORDERS = pytest.mark.parametrize(
    "date_order", [DATE_ORDER_DAY_FIRST, DATE_ORDER_MONTH_FIRST]
)


def _local(year, month, day, hour, minute, second):
    """Build the timezone-aware local datetime a myGekko date should yield."""
    return datetime(
        year, month, day, hour, minute, second, tzinfo=dt_util.DEFAULT_TIME_ZONE
    )


@BOTH_DATE_ORDERS
@pytest.mark.parametrize(
    "value",
    [
        "23.07.2026 14:47:23",
        "2026-07-23 14:47:23",
        "23/07/2026 14:47:23",
        "07/23/2026 14:47:23",
        "23-07-2026 14:47:23",
        "07-23-2026 14:47:23",
    ],
)
def test_unambiguous_date_ignores_date_order(value, date_order):
    """A date with only one valid reading is read that way with either order."""
    assert sensor.parse_mygekko_datetime(value, date_order) == _local(
        2026, 7, 23, 14, 47, 23
    )


@pytest.mark.parametrize(
    ("date_order", "month", "day"),
    [(DATE_ORDER_DAY_FIRST, 7, 5), (DATE_ORDER_MONTH_FIRST, 5, 7)],
)
@pytest.mark.parametrize("value", ["05/07/2026 10:00:00", "05-07-2026 10:00:00"])
def test_ambiguous_date_follows_date_order(value, date_order, month, day):
    """When day and month could be swapped, the date order decides."""
    assert sensor.parse_mygekko_datetime(value, date_order) == _local(
        2026, month, day, 10, 0, 0
    )


@BOTH_DATE_ORDERS
@pytest.mark.parametrize(
    "value", [None, "", "18:00:00", "20h 50m 51s", "31/31/2026 10:00:00", "not a date"]
)
def test_unparseable_date_is_none(value, date_order):
    """Missing or unparseable dates yield None, the sensor reads 'unknown'."""
    assert sensor.parse_mygekko_datetime(value, date_order) is None


@pytest.mark.parametrize(
    ("options", "month", "day"),
    [
        ({}, 7, 5),
        ({CONF_DATE_ORDER: DATE_ORDER_MONTH_FIRST}, 5, 7),
    ],
)
async def test_charge_start_sensor_uses_date_order_option(hass, options, month, day):
    """The charge start sensor reads ambiguous dates in the configured order."""
    config_entry = MockConfigEntry(
        domain=DOMAIN,
        data=MOCK_DEMO_ENTRY_DATA,
        options=options,
        entry_id="sensor_test",
        version=4,
    )
    with patch.object(
        EMobil,
        "charge_start_time",
        new_callable=PropertyMock,
        return_value="05/07/2026 10:00:00",
    ):
        config_entry.add_to_hass(hass)
        assert await hass.config_entries.async_setup(config_entry.entry_id)
        await hass.async_block_till_done()
        entity_id = er.async_get(hass).async_get_entity_id(
            "sensor", DOMAIN, "sensor_test_emobilsitem0charge_start_time"
        )
        state = hass.states.get(entity_id).state

    assert dt_util.parse_datetime(state) == _local(2026, month, day, 10, 0, 0)
