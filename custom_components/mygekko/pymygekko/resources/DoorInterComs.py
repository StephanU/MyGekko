"""MyGekko DoorInterComs implementation"""
from __future__ import annotations

from datetime import datetime
from enum import IntEnum
from enum import StrEnum

from ..data_provider import DataProviderBase
from ..data_provider import EntityValueAccessor
from . import Entity


class DoorInterCom(Entity):
    """Class for MyGekko DoorInterCom"""

    def __init__(
        self, entity_id: str, name: str, value_accessor: DoorInterComValueAccessor
    ) -> None:
        super().__init__(entity_id, name, "/door_intercom/")
        self._value_accessor = value_accessor
        self._supported_features = self._value_accessor.get_features(self)

    @property
    def supported_features(self) -> list[DoorInterComFeature]:
        """Returns the supported features"""
        return self._supported_features

    @property
    def image_url(self) -> str | None:
        """Returns the image url"""
        return self._value_accessor.get_value(self, "imagepath")

    @property
    def stream_url(self) -> str | None:
        """Returns the stream url"""
        return self._value_accessor.get_value(self, "streampath")

    @property
    def sound_mode(self) -> DoorInterComSoundMode | None:
        """Returns the sound mode"""
        value = self._value_accessor.get_value(self, "soundMode")
        return DoorInterComSoundMode(int(value)) if value is not None else None

    @property
    def action_on_ring_state(self) -> DoorInterComActionOnRingState | None:
        """Returns the action on ring state"""
        value = self._value_accessor.get_value(self, "actionOnRingState")
        return DoorInterComActionOnRingState(int(value)) if value is not None else None

    @property
    def connection_state(self) -> DoorInterComConnectionState | None:
        """Returns the connection state"""
        value = self._value_accessor.get_value(self, "connectionState")
        return DoorInterComConnectionState(int(value)) if value is not None else None

    @property
    def missed_calls(self) -> int | None:
        """Returns the missed calls"""
        value = self._value_accessor.get_value(self, "missedCallsValue")
        return int(value) if value else None

    @property
    def last_missed_call_date(self) -> datetime | None:
        """Returns the missed calls"""
        value = self._value_accessor.get_value(self, "lastMissedCallDate")
        return datetime.strptime(value, "%d.%m.%Y %H:%M:%S") if value else None


class DoorInterComFeature(IntEnum):
    """MyGekko Door Inter Com Feature"""

    ON_OFF = 0
    STREAM = 1


class DoorInterComSoundMode(IntEnum):
    """MyGekko DoorInterCom Sound Mode"""

    MUTE = 0
    RINGING = 1


class DoorInterComActionOnRingState(IntEnum):
    """MyGekko DoorInterCom Action on ring state"""

    OFF = 0
    ON = 1


class DoorInterComConnectionState(IntEnum):
    """MyGekko DoorInterCom Connection state"""

    ERROR_PROCESSING = -6
    ERROR_AUTHORIZATION = -5
    VOIP_NOT_ACTIVE = -4
    ERROR_FAV_CHECK = -3
    ERROR_PROVISIONING = -2
    ERROR_CONNECTION = -1
    NOT_SET_UP = 0
    OK = 1


class DoorInterComCommand(StrEnum):
    """MyGekko DoorInterCom Commands"""

    OPEN = "O"
    RINGING = "M1"
    MUTE = "M0"
    ACTION_ON = "A1"
    ACTION_OFF = "A0"


class DoorInterComValueAccessor(EntityValueAccessor):
    """DoorInterCom value accessor"""

    def __init__(self, data_provider: DataProviderBase):
        super().__init__()
        self._data_provider = data_provider
        self._data_provider.subscribe(self)

    def update_status(self, status, hardware):
        if status is not None and "door_intercom" in status:
            door_inter_coms = status["door_intercom"]
            for key in door_inter_coms:
                if key.startswith("item"):
                    if key not in self._data:
                        self._data[key] = {}

                    if (
                        "sumstate" in door_inter_coms[key]
                        and "value" in door_inter_coms[key]["sumstate"]
                    ):
                        (
                            self._data[key]["soundMode"],
                            self._data[key]["actionOnRingState"],
                            self._data[key]["connectionState"],
                            self._data[key]["missedCallsValue"],
                            self._data[key]["lastMissedCallDate"],
                            *_other,
                        ) = door_inter_coms[key]["sumstate"]["value"].split(
                            ";",
                        )

    def update_resources(self, resources):
        if resources is not None and "door_intercom" in resources:
            door_inter_coms = resources["door_intercom"]
            for key in door_inter_coms:
                if key.startswith("item"):
                    if key not in self._data:
                        self._data[key] = {}
                    self._data[key]["name"] = door_inter_coms[key]["name"]
                    self._data[key]["imagepath"] = door_inter_coms[key].get(
                        "imagepath", None
                    )
                    self._data[key]["streampath"] = door_inter_coms[key].get(
                        "streampath", None
                    )

    @property
    def door_inter_coms(self):
        """Returns the door intercoms read from MyGekko"""
        result: list[DoorInterCom] = []
        for key, data in self._data.items():
            if "name" not in data:
                continue
            result.append(DoorInterCom(key, data["name"], self))

        return result

    def get_features(self, door_inter_com: DoorInterCom) -> list[DoorInterComFeature]:
        """Returns the supported features"""
        result = list()

        if door_inter_com and door_inter_com.entity_id:
            if door_inter_com.entity_id in self._data:
                data = self._data[door_inter_com.entity_id]
                if "streampath" in data and data["streampath"]:
                    result.append(DoorInterComFeature.STREAM)

        return result

    async def send_command(
        self, door_inter_com: DoorInterCom, state: DoorInterComCommand
    ) -> None:
        """Sends the command"""
        if door_inter_com and door_inter_com.entity_id:
            await self._data_provider.write_data(
                door_inter_com.resource_path, str(state)
            )
