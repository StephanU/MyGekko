"""MyGekko Clocks implementation"""
from __future__ import annotations

from enum import IntEnum

from ..data_provider import DataProviderBase
from ..data_provider import EntityValueAccessor
from . import Entity


class Clock(Entity):
    """Class for MyGekko Clock"""

    def __init__(
        self, entity_id: str, name: str, value_accessor: ClockValueAccessor
    ) -> None:
        super().__init__(entity_id, name, "/clocks/")
        self._value_accessor = value_accessor

    @property
    def state(self) -> ClockState | None:
        """Returns the current state"""
        value = self._value_accessor.get_value(self, "currentState")
        return ClockState(int(value)) if value is not None else None

    @property
    def start_condition(self) -> ClockStartCondition | None:
        """Returns the current start condition state"""
        value = self._value_accessor.get_value(self, "startConditionState")
        return ClockStartCondition(int(value)) if value is not None else None

    async def set_state(self, state: ClockState):
        """Sets the state"""
        await self._value_accessor.set_state(self, state)


class ClockState(IntEnum):
    """MyGekko Clocks State"""

    OFF = 0
    ON = 1
    ON_COINCIDENCE = 2


class ClockStartCondition(IntEnum):
    """MyGekko Clocks Start Condition State"""

    OFF = 0
    ON = 1


class ClockValueAccessor(EntityValueAccessor):
    """Clocks value accessor"""

    SUM_STATE_FIELDS = ["currentState", "startConditionState", "elementInfo"]

    def __init__(self, data_provider: DataProviderBase):
        super().__init__()
        self._data_provider = data_provider
        data_provider.subscribe(self)

    def update_status(self, status, hardware):
        if status is not None and "clocks" in status:
            clocks = status["clocks"]
            for key in clocks:
                if key.startswith("item"):
                    if key not in self._data:
                        self._data[key] = {}

                    if "sumstate" in clocks[key] and "value" in clocks[key]["sumstate"]:
                        values = clocks[key]["sumstate"]["value"].split(";")
                        for name, value in zip(self.SUM_STATE_FIELDS, values):
                            self._data[key][name] = value

    def update_resources(self, resources):
        if resources is not None and "clocks" in resources:
            clocks = resources["clocks"]
            for key in clocks:
                if key.startswith("item"):
                    if key not in self._data:
                        self._data[key] = {}
                    self._data[key]["name"] = clocks[key]["name"]

    @property
    def clocks(self):
        """Returns the clocks read from MyGekko"""
        result: list[Clock] = []
        for key, data in self._data.items():
            if "name" not in data:
                continue
            result.append(Clock(key, data["name"], self))

        return result

    async def set_state(self, clock: Clock, state: ClockState) -> None:
        """Sets the state"""
        if clock and clock.entity_id:
            await self._data_provider.write_data(clock.resource_path, str(int(state)))
