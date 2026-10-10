"""MyGekko RoomTemps implementation"""
from __future__ import annotations

from enum import IntEnum

from ..data_provider import DataProviderBase
from ..data_provider import EntityValueAccessor
from . import Entity


class RoomTemp(Entity):
    """Class for MyGekko RoomTemp"""

    def __init__(
        self, entity_id: str, name: str, value_accessor: RoomTempsValueAccessor
    ) -> None:
        super().__init__(entity_id, name, "/roomtemps/")
        self._value_accessor = value_accessor
        self._supported_features = self._value_accessor.get_features(self)

    @property
    def supported_features(self) -> list[RoomTempsFeature]:
        """Returns the supported features"""
        return self._supported_features

    @property
    def working_mode(self) -> RoomTempsMode | None:
        """ "Returns the current working mode"""
        value = self._value_accessor.get_value(self, "workingMode")
        return RoomTempsMode(int(value)) if value is not None else None

    async def set_working_mode(self, working_mode: RoomTempsMode):
        """Sets the working mode"""
        await self._value_accessor.set_working_mode(self, working_mode)

    @property
    def current_temperature(self) -> float | None:
        """Returns the current  temperature"""
        value = self._value_accessor.get_value(self, "temperatureValue")
        return float(value) if value is not None else None

    @property
    def target_temperature(self) -> float | None:
        """Returns the current target temperature"""
        value = self._value_accessor.get_value(self, "temperatureSetPointValue")
        return float(value) if value is not None else None

    async def set_target_temperature(self, target_temperature: float):
        """Sets the target temperature"""
        await self._value_accessor.set_target_temperature(self, target_temperature)

    @property
    def humidity(self) -> float | None:
        """Returns the current humidity"""
        value = self._value_accessor.get_value(self, "relativeHumidityLevel")
        return float(value) if value is not None else None

    @property
    def air_quality(self) -> float | None:
        """Returns the current air quality"""
        value = self._value_accessor.get_value(self, "airQualityLevel")
        return float(value) if value is not None else None


class RoomTempsMode(IntEnum):
    """MyGekko RoomTemps Mode"""

    OFF = 1
    COMFORT = 8
    REDUCED = 16
    MANUAL = 64
    STANDBY = 256


class RoomTempsFeature(IntEnum):
    """MyGekko RoomTemps Feature"""

    TARGET_TEMPERATURE = 0
    AIR_QUALITY = 1
    HUMIDITY = 2


class RoomTempsValueAccessor(EntityValueAccessor):
    """RoomTemps value accessor"""

    def __init__(self, data_provider: DataProviderBase):
        super().__init__()
        self._data_provider = data_provider
        self._data_provider.subscribe(self)

    def update_status(self, status, hardware):
        if status is not None and "roomtemps" in status:
            room_temps = status["roomtemps"]
            for key in room_temps:
                if key.startswith("item"):
                    if key not in self._data:
                        self._data[key] = {}

                    if (
                        "sumstate" in room_temps[key]
                        and "value" in room_temps[key]["sumstate"]
                    ):
                        self.read_value(
                            key, room_temps[key]["sumstate"]["value"], hardware
                        )

    def read_value(self, key, value, hardware):
        """Reads a value based on the given hardware."""
        if hardware == "legacy":
            (
                self._data[key]["temperatureValue"],
                self._data[key]["temperatureSetPointValue"],
                self._data[key]["valveOpeningLevel"],
                self._data[key]["workingMode"],
                self._data[key]["Reserved"],
                self._data[key]["temperatureAdjustmentValue"],
                self._data[key]["coolingModeState"],
                self._data[key]["elementInfo"],
                *_other,
            ) = value.split(";")
        else:
            (
                self._data[key]["temperatureValue"],
                self._data[key]["temperatureSetPointValue"],
                self._data[key]["valveOpeningLevel"],
                self._data[key]["workingMode"],
                self._data[key]["Reserved"],
                self._data[key]["temperatureAdjustmentValue"],
                self._data[key]["coolingModeState"],
                self._data[key]["elementInfo"],
                self._data[key]["relativeHumidityLevel"],
                self._data[key]["airQualityLevel"],
                self._data[key]["floorTemperatureValue"],
                *_other,
            ) = value.split(";")

    def update_resources(self, resources):
        if resources is not None and "roomtemps" in resources:
            room_temps = resources["roomtemps"]
            for key in room_temps:
                if key.startswith("item"):
                    if key not in self._data:
                        self._data[key] = {}
                    self._data[key]["name"] = room_temps[key]["name"]

    @property
    def room_temps(self):
        """Returns the loads read from MyGekko"""
        result: list[RoomTemp] = []
        for key, data in self._data.items():
            if "name" not in data:
                continue
            result.append(RoomTemp(key, data["name"], self))

        return result

    def get_features(self, room_temp: RoomTemp) -> list[RoomTempsFeature]:
        """Returns the supported features"""
        result = list()

        if room_temp and room_temp.entity_id:
            if room_temp.entity_id in self._data:
                data = self._data[room_temp.entity_id]
                if (
                    "temperatureSetPointValue" in data
                    and data["temperatureSetPointValue"]
                ):
                    result.append(RoomTempsFeature.TARGET_TEMPERATURE)

                if "relativeHumidityLevel" in data and data["relativeHumidityLevel"]:
                    result.append(RoomTempsFeature.HUMIDITY)

                if "airQualityLevel" in data and data["airQualityLevel"]:
                    result.append(RoomTempsFeature.AIR_QUALITY)

        return result

    async def set_target_temperature(
        self, room_temp: RoomTemp, target_temperature: float
    ) -> None:
        """Sets the target temperature"""
        if room_temp and room_temp.entity_id:
            await self._data_provider.write_data(
                room_temp.resource_path, "S" + str(target_temperature)
            )

    async def set_working_mode(
        self, room_temp: RoomTemp, working_mode: RoomTempsMode
    ) -> None:
        """Sets the working mode"""
        if room_temp and room_temp.entity_id:
            await self._data_provider.write_data(
                room_temp.resource_path, "M" + str(working_mode)
            )
