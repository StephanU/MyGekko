"""Test the MyGekko alarm system (alarm panels, panel sensors, input groups)."""
import json
import pkgutil
from unittest.mock import AsyncMock
from unittest.mock import patch

import pytest
from custom_components.mygekko.alarm_system import stable_new_input_groups
from custom_components.mygekko.const import CONF_ALARM_SYSTEM_READ_ONLY
from custom_components.mygekko.const import CONF_INPUT_GROUP_INDEX
from custom_components.mygekko.const import CONF_SECURITY_AREA
from custom_components.mygekko.const import DOMAIN
from custom_components.mygekko.const import SUBENTRY_TYPE_INPUT_GROUP
from homeassistant.components.alarm_control_panel import (
    AlarmControlPanelEntityFeature,
)
from homeassistant.config_entries import ConfigSubentryData
from homeassistant.const import ATTR_ENTITY_ID
from homeassistant.const import ATTR_SUPPORTED_FEATURES
from homeassistant.const import CONF_DEVICE_CLASS
from homeassistant.const import CONF_NAME
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.exceptions import HomeAssistantError
from homeassistant.exceptions import ServiceValidationError
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers import entity_registry as er
from PyMyGekko.data_provider import DummyDataProvider
from pytest_homeassistant_custom_component.common import MockConfigEntry

from .const import MOCK_DEMO_ENTRY_DATA

ENTRY_ID = "alarm_test"

SUMSTATE_FORMAT = (
    "zone1AlarmState enum[0=ok,1=alarm]();"
    "zone1DeviceModel enum[3=complex400_V2,4=hiplex8400_V2]();"
    "zone1SharpState enum[0=noInfo,1=unsharp,2=internalSharp,3=externalSharp]();"
    "zone1InputGroupsState 128B[0x63H63L62H62L...0H0L]();"
    "zone1AlarmDeviceState enum[0=ok,1=alarm,2=fault]();"
)
ARM_COMMANDS = "2|3 (Zone 1 Internal Sharp|Zone 1 External Sharp)"


def _input_groups(*active):
    """Return the hex string myGEKKO reports for the given active input groups."""
    bits = 0
    for index in active:
        bits |= 1 << index
    return format(bits, "0128x")


class FakeAlarmSystem:
    """The alarm system of a fake myGEKKO, changed by the tests between polls."""

    def __init__(self):
        """Start with three security areas: unarmed, armed and in alarm."""
        self.names = ["SB1 EG", "SB2 1.OG", "SB8 Tresor-Lager"]
        self.commands = ARM_COMMANDS
        # alarm state, sharp state per security area
        self.areas = [(0, 1), (0, 3), (1, 3)]
        self.active_input_groups = [379]
        self.device_state = 0
        self.enabled = True
        # Active input groups of the next polls, one list per poll.
        self.polls: list[list[int]] = []

    def resources(self):
        """Return the alarmsystem node of /api/v1/var."""
        return {
            f"item{index}": {
                "name": name,
                "page": "Alarmanlage",
                "sumstate": {"value": SUMSTATE_FORMAT, "type": "STRING"},
                "scmd": {"value": self.commands, "type": "STRING"},
            }
            for index, name in enumerate(self.names)
        }

    def status(self):
        """Return the alarmsystem node of /api/v1/var/status."""
        groups = _input_groups(*self.active_input_groups)
        return {
            f"item{index}": {
                "sumstate": {
                    "value": f"{alarm};4;{sharp};{groups};{self.device_state};;;"
                }
            }
            for index, (alarm, sharp) in enumerate(self.areas)
        }


@pytest.fixture(name="alarm")
def alarm_fixture():
    """Serve the demo data plus a controllable alarm system in demo mode."""
    alarm = FakeAlarmSystem()

    async def read_data(provider):
        resources = json.loads(
            pkgutil.get_data("PyMyGekko.data_provider", "api_var_demo_data.json")
        )
        status = json.loads(
            pkgutil.get_data("PyMyGekko.data_provider", "api_var_status_demo_data.json")
        )
        resources.pop("alarmsystem", None)
        status.pop("alarmsystem", None)
        if alarm.polls:
            alarm.active_input_groups = alarm.polls.pop(0)
        if alarm.enabled:
            resources["alarmsystem"] = alarm.resources()
            status["alarmsystem"] = alarm.status()
        provider.resources = resources
        provider.status = status

    with patch.object(DummyDataProvider, "read_data", read_data):
        yield alarm


@pytest.fixture(name="written")
def written_fixture():
    """Record the commands sent to the myGEKKO."""
    with patch.object(
        DummyDataProvider, "write_data", new_callable=AsyncMock
    ) as write_data:
        yield write_data


async def _setup(hass, options=None, subentries_data=None):
    """Set up a demo mode entry."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data=MOCK_DEMO_ENTRY_DATA,
        options=options or {},
        entry_id=ENTRY_ID,
        version=4,
        subentries_data=subentries_data or (),
    )
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    return entry


def _entity_id(hass, domain, unique_id):
    return er.async_get(hass).async_get_entity_id(domain, DOMAIN, unique_id)


def _panel_entity_id(hass, item):
    return _entity_id(hass, "alarm_control_panel", f"{ENTRY_ID}_alarm_system{item}")


async def _poll(hass):
    await hass.data[DOMAIN][ENTRY_ID].async_refresh()
    await hass.async_block_till_done()


async def test_security_areas_as_alarm_panels(hass, alarm):
    """Each security area is an alarm panel showing its arming state."""
    await _setup(hass)

    states = [hass.states.get(_panel_entity_id(hass, f"item{i}")) for i in range(3)]
    assert [state.state for state in states] == ["disarmed", "armed_away", "triggered"]
    assert states[0].name == "SB1 EG"
    assert states[0].attributes[ATTR_SUPPORTED_FEATURES] == (
        AlarmControlPanelEntityFeature.ARM_HOME | AlarmControlPanelEntityFeature.ARM_AWAY
    )

    alarm.areas = [(0, 2), (0, 0), (0, 1)]
    await _poll(hass)
    states = [hass.states.get(_panel_entity_id(hass, f"item{i}")) for i in range(3)]
    assert [state.state for state in states] == ["armed_home", "unknown", "disarmed"]


async def test_security_areas_belong_to_the_panel_device(hass, alarm):
    """The security area devices are connected through the panel device."""
    await _setup(hass)

    device_registry = dr.async_get(hass)
    panel = device_registry.async_get_device_by_identifier(
        (DOMAIN, f"{ENTRY_ID}_alarm_system_panel"), ENTRY_ID
    )
    assert panel.manufacturer == "TELENOT"
    assert panel.model == "hiplex 8400"

    area = device_registry.async_get_device_by_identifier(
        (DOMAIN, f"{ENTRY_ID}_alarm_systemitem0"), ENTRY_ID
    )
    assert area.name == "SB1 EG"
    assert area.via_device_id == panel.id


async def test_arm_away_shows_arming_until_the_panel_reports_it(hass, alarm, written):
    """Arming sends the command and shows "arming" until the panel is armed."""
    await _setup(hass)
    entity_id = _panel_entity_id(hass, "item0")

    await hass.services.async_call(
        "alarm_control_panel",
        "alarm_arm_away",
        {ATTR_ENTITY_ID: entity_id},
        blocking=True,
    )
    written.assert_awaited_once_with("/alarmsystem/item0", "3")
    # The refresh after the command still shows the unarmed area.
    assert hass.states.get(entity_id).state == "arming"

    alarm.areas[0] = (0, 3)
    await _poll(hass)
    assert hass.states.get(entity_id).state == "armed_away"


async def test_arm_home_sends_internal_arming(hass, alarm, written):
    """Arming home arms the security area internally."""
    await _setup(hass)

    await hass.services.async_call(
        "alarm_control_panel",
        "alarm_arm_home",
        {ATTR_ENTITY_ID: _panel_entity_id(hass, "item0")},
        blocking=True,
    )
    written.assert_awaited_once_with("/alarmsystem/item0", "2")


async def test_disarm_is_rejected_without_disarm_command(hass, alarm, written):
    """Disarming is not offered by the myGEKKO Query API, so nothing is sent."""
    await _setup(hass)

    with pytest.raises(ServiceValidationError) as error:
        await hass.services.async_call(
            "alarm_control_panel",
            "alarm_disarm",
            {ATTR_ENTITY_ID: _panel_entity_id(hass, "item1")},
            blocking=True,
        )
    assert error.value.translation_key == "alarm_system_command_not_supported"
    written.assert_not_awaited()


async def test_disarm_when_announced(hass, alarm, written):
    """A myGEKKO announcing the disarm command gets it sent."""
    alarm.commands = "1|2|3 (Unsharp|Internal Sharp|External Sharp)"
    await _setup(hass)

    await hass.services.async_call(
        "alarm_control_panel",
        "alarm_disarm",
        {ATTR_ENTITY_ID: _panel_entity_id(hass, "item1")},
        blocking=True,
    )
    written.assert_awaited_once_with("/alarmsystem/item1", "1")


async def test_read_only(hass, alarm, written):
    """Read only alarm panels offer and send no command."""
    await _setup(hass, options={CONF_ALARM_SYSTEM_READ_ONLY: True})
    entity_id = _panel_entity_id(hass, "item0")

    assert hass.states.get(entity_id).attributes[ATTR_SUPPORTED_FEATURES] == 0

    with pytest.raises(HomeAssistantError):
        await hass.services.async_call(
            "alarm_control_panel",
            "alarm_arm_away",
            {ATTR_ENTITY_ID: entity_id},
            blocking=True,
        )
    with pytest.raises(ServiceValidationError) as error:
        await hass.services.async_call(
            "alarm_control_panel",
            "alarm_disarm",
            {ATTR_ENTITY_ID: entity_id},
            blocking=True,
        )
    assert error.value.translation_key == "alarm_system_read_only"
    written.assert_not_awaited()


async def test_panel_sensors(hass, alarm):
    """The panel state is a sensor, the active input groups a disabled one."""
    await _setup(hass)

    state_entity_id = _entity_id(hass, "sensor", f"{ENTRY_ID}_alarm_system_panel_state")
    assert hass.states.get(state_entity_id).state == "ok"

    alarm.device_state = 2
    await _poll(hass)
    assert hass.states.get(state_entity_id).state == "fault"

    active_entity_id = _entity_id(
        hass, "sensor", f"{ENTRY_ID}_alarm_system_panel_active_input_groups"
    )
    entry = er.async_get(hass).async_get(active_entity_id)
    assert entry.disabled_by is er.RegistryEntryDisabler.INTEGRATION


async def test_active_input_groups_sensor(hass, alarm):
    """The active input groups sensor lists the indexes to configure."""
    await _setup(hass)
    entity_id = _entity_id(
        hass, "sensor", f"{ENTRY_ID}_alarm_system_panel_active_input_groups"
    )
    er.async_get(hass).async_update_entity(entity_id, disabled_by=None)
    await hass.config_entries.async_reload(ENTRY_ID)
    await hass.async_block_till_done()

    alarm.active_input_groups = [0, 5, 379]
    await _poll(hass)
    state = hass.states.get(entity_id)
    assert state.state == "3"
    assert state.attributes["active_input_groups"] == [0, 5, 379]


async def test_input_group_binary_sensor(hass, alarm):
    """An input group subentry is a binary sensor, on while it is active."""
    await _setup(
        hass,
        subentries_data=[
            ConfigSubentryData(
                data={
                    CONF_INPUT_GROUP_INDEX: 379,
                    CONF_DEVICE_CLASS: "door",
                    CONF_SECURITY_AREA: "item0",
                },
                subentry_id="main_entrance",
                subentry_type=SUBENTRY_TYPE_INPUT_GROUP,
                title="Main entrance",
                unique_id="379",
            )
        ],
    )
    entity_id = _entity_id(hass, "binary_sensor", f"{ENTRY_ID}_main_entrance")
    state = hass.states.get(entity_id)
    assert state.state == "on"
    assert state.name == "Main entrance"
    assert state.attributes["device_class"] == "door"

    alarm.active_input_groups = []
    await _poll(hass)
    assert hass.states.get(entity_id).state == "off"

    device_registry = dr.async_get(hass)
    device = device_registry.async_get(er.async_get(hass).async_get(entity_id).device_id)
    assert device.name == "Main entrance"
    assert device.config_subentry_id == "main_entrance"
    area = device_registry.async_get_device_by_identifier(
        (DOMAIN, f"{ENTRY_ID}_alarm_systemitem0"), ENTRY_ID
    )
    assert device.via_device_id == area.id
    assert area.config_subentry_id is None


async def _start_input_group_flow(hass, entry, menu_choice):
    """Start adding an input group and pick learning or manual entry."""
    result = await hass.config_entries.subentries.async_init(
        (entry.entry_id, SUBENTRY_TYPE_INPUT_GROUP), context={"source": "user"}
    )
    assert result["type"] is FlowResultType.MENU
    return await hass.config_entries.subentries.async_configure(
        result["flow_id"], {"next_step_id": menu_choice}
    )


async def test_add_and_change_input_group(hass, alarm):
    """Input groups are added and changed through the subentry flow."""
    entry = await _setup(hass)

    result = await _start_input_group_flow(hass, entry, "manual")
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "manual"
    result = await hass.config_entries.subentries.async_configure(
        result["flow_id"],
        {CONF_INPUT_GROUP_INDEX: 379, CONF_NAME: "Main entrance", CONF_DEVICE_CLASS: "door"},
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    await hass.async_block_till_done(wait_background_tasks=True)

    (subentry,) = entry.subentries.values()
    entity_id = _entity_id(hass, "binary_sensor", f"{ENTRY_ID}_{subentry.subentry_id}")
    assert hass.states.get(entity_id).state == "on"

    # The same input group cannot be added twice.
    result = await _start_input_group_flow(hass, entry, "manual")
    result = await hass.config_entries.subentries.async_configure(
        result["flow_id"], {CONF_INPUT_GROUP_INDEX: 379, CONF_NAME: "Again"}
    )
    assert result["errors"] == {CONF_INPUT_GROUP_INDEX: "input_group_already_configured"}

    result = await entry.start_subentry_reconfigure_flow(hass, subentry.subentry_id)
    result = await hass.config_entries.subentries.async_configure(
        result["flow_id"],
        {CONF_INPUT_GROUP_INDEX: 5, CONF_NAME: "Window", CONF_DEVICE_CLASS: "window"},
    )
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "reconfigure_successful"
    await hass.async_block_till_done()

    state = hass.states.get(entity_id)
    assert state.state == "off"
    assert state.attributes["device_class"] == "window"
    assert entry.subentries[subentry.subentry_id].data[CONF_INPUT_GROUP_INDEX] == 5


async def test_options_flow_sets_read_only(hass, alarm):
    """The read only option can be changed later and reloads the entry."""
    entry = await _setup(hass)

    result = await hass.config_entries.options.async_init(entry.entry_id)
    assert result["type"] is FlowResultType.FORM
    result = await hass.config_entries.options.async_configure(
        result["flow_id"], {CONF_ALARM_SYSTEM_READ_ONLY: True}
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    await hass.async_block_till_done()

    assert entry.options[CONF_ALARM_SYSTEM_READ_ONLY] is True
    state = hass.states.get(_panel_entity_id(hass, "item0"))
    assert state.attributes[ATTR_SUPPORTED_FEATURES] == 0


async def test_without_alarm_system(hass, alarm):
    """A controller without alarm system gets no alarm entities and flows."""
    alarm.enabled = False
    entry = await _setup(hass)

    assert not hass.states.async_entity_ids("alarm_control_panel")
    assert not dr.async_get(hass).async_get_device_by_identifier(
        (DOMAIN, f"{ENTRY_ID}_alarm_system_panel"), ENTRY_ID
    )

    result = await hass.config_entries.options.async_init(entry.entry_id)
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "no_options"

    result = await hass.config_entries.subentries.async_init(
        (entry.entry_id, SUBENTRY_TYPE_INPUT_GROUP), context={"source": "user"}
    )
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "no_alarm_system"


def test_stable_new_input_groups():
    """Only input groups new since the baseline and active in a row count."""
    baseline = {1, 2, 3}
    assert stable_new_input_groups(baseline, [{1, 212}], 2) == set()
    assert stable_new_input_groups(baseline, [{1, 212}, {2, 212}], 2) == {212}
    # Flickering between polls is not stable.
    assert stable_new_input_groups(baseline, [{212}, {213}], 2) == set()
    # Only the last polls count.
    assert stable_new_input_groups(baseline, [{5}, {5, 212}, {212}], 2) == {212}


async def _run_learning(hass, alarm, baseline_polls, detect_polls):
    """Add an input group by learning, return the step after the detection."""
    entry = await _setup(hass)
    alarm.polls = [*baseline_polls, *detect_polls]

    result = await _start_input_group_flow(hass, entry, "learn")
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "learn"

    result = await hass.config_entries.subentries.async_configure(result["flow_id"], {})
    assert result["type"] is FlowResultType.SHOW_PROGRESS
    assert result["progress_action"] == "learn_baseline"
    await hass.async_block_till_done()

    result = await hass.config_entries.subentries.async_configure(result["flow_id"])
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "learn_trigger"

    result = await hass.config_entries.subentries.async_configure(result["flow_id"], {})
    assert result["type"] is FlowResultType.SHOW_PROGRESS
    assert result["progress_action"] == "learn_detect"
    await hass.async_block_till_done()

    return entry, await hass.config_entries.subentries.async_configure(
        result["flow_id"]
    )


# Motion detectors 120 and 166 flicker while the baseline is recorded.
BASELINE_POLLS = [[120], [120, 166], [], [166], [120], []]


@pytest.fixture(name="fast_learning")
def fast_learning_fixture():
    """Learn without waiting between the polls."""
    with patch("custom_components.mygekko.alarm_system.LEARN_POLL_INTERVAL", 0):
        yield


async def test_learn_input_group(hass, alarm, fast_learning):
    """A triggered input group is found despite flickering motion detectors."""
    entry, result = await _run_learning(
        hass, alarm, BASELINE_POLLS, [[120, 212], [166, 212]]
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "learned"
    assert result["description_placeholders"] == {"index": "212"}
    # The polls stop as soon as one input group is found.
    assert alarm.polls == []

    result = await hass.config_entries.subentries.async_configure(
        result["flow_id"],
        {CONF_INPUT_GROUP_INDEX: 212, CONF_NAME: "Window", CONF_DEVICE_CLASS: "window"},
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    (subentry,) = entry.subentries.values()
    assert subentry.data[CONF_INPUT_GROUP_INDEX] == 212
    assert subentry.title == "Window"


async def test_learn_input_group_found_none(hass, alarm, fast_learning):
    """Without a new stable input group the index is entered by hand."""
    _, result = await _run_learning(
        hass, alarm, BASELINE_POLLS, [[120], [166, 212], [120, 213]] + [[]] * 9
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "manual"
    assert result["errors"] == {"base": "no_input_group_found"}


async def test_learn_input_group_found_several(hass, alarm, fast_learning):
    """Several new stable input groups are listed for manual entry."""
    _, result = await _run_learning(
        hass, alarm, BASELINE_POLLS, [[212, 213]] * 12
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "manual"
    assert result["errors"] == {"base": "multiple_input_groups_found"}
    assert result["description_placeholders"] == {"indexes": "212, 213"}
