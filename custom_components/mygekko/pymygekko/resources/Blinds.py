"""MyGekko Blinds implementation"""
from __future__ import annotations

from enum import IntEnum

from ..data_provider import DataProviderBase
from ..data_provider import EntityValueAccessor
from . import Entity


class Blind(Entity):
    """Class for MyGekko Blind"""

    def __init__(
        self, entity_id: str, name: str, value_accessor: BlindValueAccessor
    ) -> None:
        super().__init__(entity_id, name, "/blinds/")
        self._value_accessor = value_accessor
        self._supported_features = self._value_accessor.get_features(self)

    @property
    def supported_features(self) -> list[BlindFeature]:
        """Returns the supported features"""
        return self._supported_features

    @property
    def position(self) -> float | None:
        """Returns the current position"""
        value = self._value_accessor.get_value(self, "positionLevel")
        return float(value) if value is not None else None

    async def set_position(self, position: float):
        """Sets the position"""
        await self._value_accessor.set_position(self, position)

    @property
    def state(self) -> BlindState | None:
        """Returns the current state"""
        value = self._value_accessor.get_value(self, "currentState")
        return BlindState(int(value)) if value is not None else None

    async def set_state(self, state: BlindState):
        """Sets the state"""
        await self._value_accessor.set_state(self, state)

    @property
    def tilt_position(self) -> float | None:
        """Returns the current tilt position"""
        value = self._value_accessor.get_value(self, "rotationLevel")
        return float(value) if value is not None else None

    async def set_tilt_position(self, position: float):
        """Sets the tilt position"""
        await self._value_accessor.set_tilt_position(self, position)

    @property
    def element_info(self) -> BlindElementInfo | None:
        """Returns the element info"""
        value = self._value_accessor.get_value(self, "elementInfo")
        return BlindElementInfo(float(value)) if value is not None else None


class BlindState(IntEnum):
    """MyGekko Blinds State"""

    HOLD_DOWN = -2
    DOWN = -1
    STOP = 0
    UP = 1
    HOLD_UP = 2


class BlindFeature(IntEnum):
    """MyGekko Blinds Feature"""

    OPEN_CLOSE_STOP = 0
    SET_POSITION = 1
    SET_TILT_POSITION = 2
    OPEN_CLOSE = 3


class BlindElementInfo(IntEnum):
    """MyGekko Blinds Element Info"""

    OK = 0
    MANUAL_OFF = 1
    MANUAL_ON = 2
    LOCKED = 3
    ALARM = 4


class BlindValueAccessor(EntityValueAccessor):
    """Blind value accessor"""

    def __init__(self, data_provider: DataProviderBase):
        super().__init__()
        self._data_provider = data_provider
        self._data_provider.subscribe(self)

    def update_status(self, status, hardware):
        if status is not None and "blinds" in status:
            blinds = status["blinds"]
            for key in blinds:
                if key.startswith("item"):
                    if key not in self._data:
                        self._data[key] = {}

                    if "sumstate" in blinds[key] and "value" in blinds[key]["sumstate"]:
                        (
                            self._data[key]["currentState"],
                            self._data[key]["positionLevel"],
                            self._data[key]["rotationLevel"],
                            self._data[key]["elementInfo"],
                            self._data[key]["rotationRange"],
                            *_other,
                        ) = blinds[key]["sumstate"]["value"].split(
                            ";",
                        )

                if key.startswith("group"):
                    if key not in self._data:
                        self._data[key] = {}

                    if "sumstate" in blinds[key] and "value" in blinds[key]["sumstate"]:
                        (
                            self._data[key]["currentState"],
                            *_other,
                        ) = blinds[key][
                            "sumstate"
                        ]["value"].split(
                            ";",
                        )

    def update_resources(self, resources):
        if resources is not None and "blinds" in resources:
            blinds = resources["blinds"]
            for key in blinds:
                if key.startswith("item"):
                    if key not in self._data:
                        self._data[key] = {}
                    self._data[key]["name"] = blinds[key]["name"]

                if key.startswith("group"):
                    if key not in self._data:
                        self._data[key] = {}
                    self._data[key]["name"] = blinds[key]["name"]

    @property
    def blinds(self):
        """Returns the blinds read from MyGekko"""
        result: list[Blind] = []
        for key, data in self._data.items():
            if "name" not in data:
                continue
            result.append(Blind(key, data["name"], self))

        return result

    def get_features(self, blind: Blind) -> list[BlindFeature]:
        """Returns the supported features"""
        result = list()

        if blind and blind.entity_id:
            if blind.entity_id in self._data:
                data = self._data[blind.entity_id]
                if blind.entity_id.startswith("group"):
                    # open/close feature is the only feature for groups
                    result.append(BlindFeature.OPEN_CLOSE)
                    return result

                if "currentState" in data and data["currentState"]:
                    result.append(BlindFeature.OPEN_CLOSE_STOP)

                if "positionLevel" in data and data["positionLevel"]:
                    result.append(BlindFeature.SET_POSITION)

                if "rotationLevel" in data and data["rotationLevel"]:
                    result.append(BlindFeature.SET_TILT_POSITION)

        return result

    async def set_position(self, blind: Blind, position: float) -> None:
        """Sets the position"""
        if blind and blind.entity_id and position >= 0 and position <= 100.0:
            await self._data_provider.write_data(
                blind.resource_path, "P" + str(position)
            )

    async def set_tilt_position(self, blind: Blind, position: float) -> None:
        """Sets the tilt position"""
        if blind and blind.entity_id and position >= 0 and position <= 100.0:
            await self._data_provider.write_data(
                blind.resource_path, "S" + str(position)
            )

    async def set_state(self, blind: Blind, state: BlindState) -> None:
        """Sets the state"""
        if blind and blind.entity_id:
            await self._data_provider.write_data(blind.resource_path, str(state))
