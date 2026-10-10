"""MyGekko Hotwater_systems implementation"""
from __future__ import annotations

from enum import IntEnum

from ..data_provider import DataProviderBase
from ..data_provider import EntityValueAccessor
from . import Entity


class HotWaterSystem(Entity):
    """Class for MyGekko HotWaterSystem"""

    def __init__(
        self, entity_id: str, name: str, value_accessor: HotWaterSystemValueAccessor
    ) -> None:
        super().__init__(entity_id, name, "/hotwater_systems/")
        self._value_accessor = value_accessor
        self._supported_features = self._value_accessor.get_features(self)

    @property
    def supported_features(self) -> list[HotWaterSystemFeature]:
        """Returns the supported features"""
        return self._supported_features

    @property
    def state(self) -> HotWaterSystemState | None:
        """Return the current state"""
        value = self._value_accessor.get_value(self, "state")
        return HotWaterSystemState(int(value)) if value is not None else None

    async def set_state(self, state: HotWaterSystemState):
        """Sets the state"""
        await self._value_accessor.set_state(self, state)

    @property
    def target_temperature(self) -> float | None:
        """Return the current target temperature"""
        value = self._value_accessor.get_value(self, "setpointTemp")
        return float(value) if value is not None else None

    async def set_target_temperature(self, target_temperature: float):
        """Sets the target temperature"""
        await self._value_accessor.set_target_temperature(self, target_temperature)

    @property
    def current_temperature_top(self) -> float | None:
        """Return the current top temperature"""
        value = self._value_accessor.get_value(self, "topTemp")
        return float(value) if value is not None else None

    @property
    def current_temperature_bottom(self) -> float | None:
        """Return the current bottom temperature"""
        value = self._value_accessor.get_value(self, "bottomTemp")
        return float(value) if value is not None else None


class HotWaterSystemState(IntEnum):
    """MyGekko HotWaterSystem state"""

    OFF = 0
    ON = 1


class HotWaterSystemFeature(IntEnum):
    """MyGekko HotWaterSystem Feature"""

    ON_OFF = 0
    TARGET_TEMPERATURE = 1
    BOTTOM_TEMPERATURE = 2
    TOP_TEMPERATURE = 3


class HotWaterSystemValueAccessor(EntityValueAccessor):
    """HotWaterSystem value accessor"""

    def __init__(self, data_provider: DataProviderBase):
        super().__init__()
        self._data_provider = data_provider
        data_provider.subscribe(self)

    def update_status(self, status, hardware):
        if status is not None and "hotwater_systems" in status:
            hotwater_systems = status["hotwater_systems"]
            for key in hotwater_systems:
                if key.startswith("item"):
                    if key not in self._data:
                        self._data[key] = {}

                    if (
                        "sumstate" in hotwater_systems[key]
                        and "value" in hotwater_systems[key]["sumstate"]
                    ):
                        (
                            self._data[key]["type"],
                            self._data[key]["cooling"],
                            self._data[key]["setpointTemp"],
                            self._data[key]["topTemp"],
                            self._data[key]["bottomTemp"],
                            self._data[key]["collectorTemp"],
                            self._data[key]["state"],
                            self._data[key]["sum"],
                            *_other,
                        ) = hotwater_systems[key]["sumstate"]["value"].split(";")

    def update_resources(self, resources):
        if resources is not None and "hotwater_systems" in resources:
            hotwater_systems = resources["hotwater_systems"]
            for key in hotwater_systems:
                if key.startswith("item"):
                    if key not in self._data:
                        self._data[key] = {}
                    self._data[key]["name"] = hotwater_systems[key]["name"]

    @property
    def hotwater_systems(self):
        """Returns the hotwater_systems read from MyGekko"""
        result: list[HotWaterSystem] = []
        for key, data in self._data.items():
            if "name" not in data:
                continue
            result.append(HotWaterSystem(key, data["name"], self))

        return result

    def get_features(
        self, hotwater_system: HotWaterSystem
    ) -> list[HotWaterSystemFeature]:
        """Returns the supported features"""
        result = list()

        if hotwater_system and hotwater_system.entity_id:
            if hotwater_system.entity_id in self._data:
                data = self._data[hotwater_system.entity_id]
                if "state" in data and data["state"]:
                    result.append(HotWaterSystemFeature.ON_OFF)
                if "setpointTemp" in data and data["setpointTemp"]:
                    result.append(HotWaterSystemFeature.TARGET_TEMPERATURE)
                if "bottomTemp" in data and data["bottomTemp"]:
                    result.append(HotWaterSystemFeature.BOTTOM_TEMPERATURE)
                if "topTemp" in data and data["topTemp"]:
                    result.append(HotWaterSystemFeature.TOP_TEMPERATURE)

        return result

    async def set_state(
        self, hotwater_system: HotWaterSystem, state: HotWaterSystemState
    ) -> None:
        """Sets the state"""
        if hotwater_system and hotwater_system.entity_id:
            await self._data_provider.write_data(
                hotwater_system.resource_path, str(state)
            )

    async def set_target_temperature(
        self, hotwater_system: HotWaterSystem, target_temperature: float
    ) -> None:
        """Sets the target temperature"""
        if hotwater_system and hotwater_system.entity_id:
            await self._data_provider.write_data(
                hotwater_system.resource_path, "T" + str(target_temperature)
            )
