"""MyGekko Loads implementation"""
from __future__ import annotations

from enum import IntEnum

from ..data_provider import DataProviderBase
from ..data_provider import EntityValueAccessor
from . import Entity


class Load(Entity):
    """Class for MyGekko Load"""

    def __init__(
        self, entity_id: str, name: str, value_accessor: LoadValueAccessor
    ) -> None:
        super().__init__(entity_id, name, "/loads/")
        self._value_accessor = value_accessor
        self._supported_features = self._value_accessor.get_features(self)

    @property
    def supported_features(self) -> list[LoadFeature]:
        """Returns the supported features"""
        return self._supported_features

    @property
    def state(self) -> LoadState | None:
        """Returns the current state"""
        value = self._value_accessor.get_value(self, "currentState")
        return LoadState(int(value)) if value is not None else None

    async def set_state(self, state: LoadState):
        """Sets the state"""
        await self._value_accessor.set_state(self, state)


class LoadState(IntEnum):
    """MyGekko Loads State"""

    OFF = 0
    ON_IMPULSE = 1
    ON_PERMANENT = 2


class LoadFeature(IntEnum):
    """MyGekko Loads Feature"""

    ON_OFF = 0


class LoadValueAccessor(EntityValueAccessor):
    """Loads value accessor"""

    def __init__(self, data_provider: DataProviderBase):
        super().__init__()
        self._data_provider = data_provider
        data_provider.subscribe(self)

    def update_status(self, status, hardware):
        if status is not None and "loads" in status:
            loads = status["loads"]
            for key in loads:
                if key.startswith("item"):
                    if key not in self._data:
                        self._data[key] = {}

                    if "sumstate" in loads[key] and "value" in loads[key]["sumstate"]:
                        (
                            self._data[key]["currentState"],
                            self._data[key]["elementInfo"],
                            *_other,
                        ) = loads[key]["sumstate"]["value"].split(";")

    def update_resources(self, resources):
        if resources is not None and "loads" in resources:
            loads = resources["loads"]
            for key in loads:
                if key.startswith("item"):
                    if key not in self._data:
                        self._data[key] = {}
                    self._data[key]["name"] = loads[key]["name"]

    @property
    def loads(self):
        """Returns the loads read from MyGekko"""
        result: list[Load] = []
        for key, data in self._data.items():
            if "name" not in data:
                continue
            result.append(Load(key, data["name"], self))

        return result

    def get_features(self, load: Load) -> list[LoadFeature]:
        """Returns the supported features"""
        result = list()

        if load and load.entity_id:
            if load.entity_id in self._data:
                data = self._data[load.entity_id]
                if "currentState" in data and data["currentState"]:
                    result.append(LoadFeature.ON_OFF)
        return result

    async def set_state(self, load: Load, state: LoadState) -> None:
        """Sets the state"""
        if load and load.entity_id:
            await self._data_provider.write_data(load.resource_path, str(state))
