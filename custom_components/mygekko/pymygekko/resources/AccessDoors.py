"""MyGekko AccessDoors implementation"""
from __future__ import annotations

from enum import IntEnum

from ..data_provider import DataProviderBase
from ..data_provider import EntityValueAccessor
from . import Entity


class AccessDoor(Entity):
    """Class for MyGekko AccessDoor"""

    def __init__(
        self, entity_id: str, name: str, value_accessor: AccessDoorValueAccessor
    ) -> None:
        super().__init__(entity_id, name, "/accessdoors/")
        self._value_accessor = value_accessor
        self._supported_features = self._value_accessor.get_features(self)

    @property
    def supported_features(self) -> list[AccessDoorFeature]:
        """Returns the supported features"""
        return self._supported_features

    @property
    def access_state(self) -> AccessDoorAccessState | None:
        """Returns the current access state"""
        value = self._value_accessor.get_value(self, "accessState")
        return AccessDoorAccessState(int(value)) if value is not None else None

    @property
    def access_type(self) -> AccessDoorAccessType | None:
        """Returns the current access type"""
        value = self._value_accessor.get_value(self, "accessType")
        return AccessDoorAccessType(int(value)) if value is not None else None

    async def set_state(self, state: AccessDoorCommand):
        """Sets the state"""
        await self._value_accessor.set_state(self, state)

    @property
    def element_info(self) -> AccessDoorElementInfo | None:
        """Returns the element info"""
        value = self._value_accessor.get_value(self, "elementInfo")
        return AccessDoorElementInfo(float(value)) if value is not None else None


class AccessDoorAccessState(IntEnum):
    """MyGekko AccessDoors Access State"""

    CLOSED = 0
    OPEN = 1


class AccessDoorAccessType(IntEnum):
    """MyGekko AccessDoors State"""

    DOOR = 0
    GATE_CONTROL = 1
    BARRIER_CONTROL = 2
    GATE_OPERATION = 3
    MYGEKKO_NET_REMOTE_DOOR = 10


class AccessDoorState(IntEnum):
    """MyGekko AccessDoors State"""

    CLOSE = 0
    OPEN = 1
    HOLD_DOWN = 2
    PARTIALLY_OPEN = 3
    PARTIALLY_HOLD_OPEN = 4


class AccessDoorCommand(IntEnum):
    """MyGekko AccessDoors Command"""

    STOP = -3
    CLOSE = -2
    LOCK = -1
    OPEN = 1
    HOLD_OPEN = 2


class AccessDoorFeature(IntEnum):
    """MyGekko AccessDoors Feature"""

    OPEN = 0


class AccessDoorElementInfo(IntEnum):
    """MyGekko AccessDoors Element Info"""

    OK = 0
    MANUAL_OFF = 1
    MANUAL_ON = 2
    LOCKED = 3
    ALARM = 4


class AccessDoorValueAccessor(EntityValueAccessor):
    """AccessDoor value accessor"""

    def __init__(self, data_provider: DataProviderBase):
        super().__init__()
        self._data_provider = data_provider
        self._data_provider.subscribe(self)

    def update_status(self, status, hardware):
        if status is not None and "accessdoors" in status:
            access_doors = status["accessdoors"]
            for key in access_doors:
                if key.startswith("item"):
                    if key not in self._data:
                        self._data[key] = {}

                    if (
                        "sumstate" in access_doors[key]
                        and "value" in access_doors[key]["sumstate"]
                    ):
                        (
                            self._data[key]["accessControllerActionState"],
                            self._data[key]["elementInfo"],
                            self._data[key]["accessState"],
                            self._data[key]["gateRuntimeLevel"],
                            self._data[key]["accessType"],
                            *_other,
                        ) = access_doors[key]["sumstate"]["value"].split(
                            ";",
                        )

    def update_resources(self, resources):
        if resources is not None and "accessdoors" in resources:
            access_doors = resources["accessdoors"]
            for key in access_doors:
                if key.startswith("item"):
                    if key not in self._data:
                        self._data[key] = {}
                    self._data[key]["name"] = access_doors[key]["name"]

    @property
    def access_doors(self):
        """Returns the access doors read from MyGekko"""
        result: list[AccessDoor] = []
        for key, data in self._data.items():
            if "name" not in data:
                continue
            result.append(AccessDoor(key, data["name"], self))

        return result

    def get_features(self, door: AccessDoor) -> list[AccessDoorFeature]:
        """Returns the supported features"""
        result = list()

        if door and door.entity_id:
            if door.entity_id in self._data:
                data = self._data[door.entity_id]
                if (
                    "accessControllerActionState" in data
                    and data["accessControllerActionState"]
                ):
                    result.append(AccessDoorFeature.OPEN)

        return result

    async def set_state(self, door: AccessDoor, state: AccessDoorCommand) -> None:
        """Sets the state"""
        if door and door.entity_id:
            await self._data_provider.write_data(door.resource_path, str(state))
