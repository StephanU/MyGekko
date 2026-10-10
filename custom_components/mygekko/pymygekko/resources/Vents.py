"""MyGekko Vents implementation"""
from __future__ import annotations

from enum import IntEnum

from ..data_provider import DataProviderBase
from ..data_provider import EntityValueAccessor
from . import Entity


class Vent(Entity):
    """Class for MyGekko Vents"""

    def __init__(
        self, entity_id: str, name: str, value_accessor: VentValueAccessor
    ) -> None:
        super().__init__(entity_id, name, "/vents/")
        self._value_accessor = value_accessor
        self._supported_features = self._value_accessor.get_features(self)

    @property
    def supported_features(self) -> list[VentFeature]:
        """Returns the supported features"""
        return self._supported_features

    @property
    def element_info(self) -> VentElementInfo | None:
        """Returns the element info"""
        value = self._value_accessor.get_value(self, "elementInfo")
        return VentElementInfo(int(value)) if value is not None else None

    @property
    def working_level(self) -> VentWorkingLevel | None:
        """Returns the current working level"""
        value = self._value_accessor.get_value(self, "workingLevel")
        return VentWorkingLevel(int(value)) if value is not None else None

    @property
    def maximum_working_level(self) -> VentWorkingLevel | None:
        """Returns the maximum working level"""
        value = self._value_accessor.get_value(self, "maximumWorkingLevel")
        return VentWorkingLevel(int(value)) if value is not None else None

    async def set_working_level(self, working_level: VentWorkingLevel):
        """Sets the working level"""
        await self._value_accessor.set_working_level(self, working_level)

    @property
    def device_model(self) -> VentDeviceModel | None:
        """Returns the device_model"""
        value = self._value_accessor.get_value(self, "deviceModel")
        return VentDeviceModel(int(value)) if value is not None else None

    @property
    def relative_humidity(self) -> float | None:
        """Returns the relative humidity"""
        value = self._value_accessor.get_value(self, "relativeHumidityLevel")
        return float(value) if value is not None else None

    @property
    def air_quality(self) -> float | None:
        """Returns the air quality"""
        value = self._value_accessor.get_value(self, "airQualityLevel")
        return float(value) if value is not None else None

    @property
    def co2(self) -> float | None:
        """Returns the co2 level"""
        value = self._value_accessor.get_value(self, "co2Value")
        return float(value) if value is not None else None

    @property
    def supply_air_temperature(self) -> float | None:
        """Returns the supply air temperature"""
        value = self._value_accessor.get_value(self, "supplyAirTemperatureValue")
        return float(value) if value is not None else None

    @property
    def exhaust_air_temperature(self) -> float | None:
        """Returns the exhaust air temperature"""
        value = self._value_accessor.get_value(self, "exhaustAirTemperatureValue")
        return float(value) if value is not None else None

    @property
    def outside_air_temperature(self) -> float | None:
        """Returns the outside air temperature"""
        value = self._value_accessor.get_value(self, "outsideAirTemperatureValue")
        return float(value) if value is not None else None

    @property
    def outgoing_air_temperature(self) -> float | None:
        """Returns the outgoing air temperature"""
        value = self._value_accessor.get_value(self, "outgoingAirTemperatureValue")
        return float(value) if value is not None else None

    @property
    def supply_air_working_level(self) -> float | None:
        """Returns the supply air working level"""
        value = self._value_accessor.get_value(self, "supplyAirWorkingLevel")
        return float(value) if value is not None else None

    @property
    def exhaust_air_working_level(self) -> float | None:
        """Returns the exhaust air working level"""
        value = self._value_accessor.get_value(self, "exhaustAirWorkingLevel")
        return float(value) if value is not None else None

    @property
    def cooling_mode(self) -> VentCoolingMode | None:
        """Returns the cooling mode"""
        value = self._value_accessor.get_value(self, "coolingModeState")
        return VentCoolingMode(int(value)) if value is not None else None

    async def set_cooling_mode(self, cooling_mode: VentCoolingMode):
        """Sets the cooling mode"""
        await self._value_accessor.set_cooling_mode(self, cooling_mode)

    @property
    def dehumid_mode(self) -> VentDehumidMode | None:
        """Returns the dehumid mode"""
        value = self._value_accessor.get_value(self, "dehumidModeState")
        return VentDehumidMode(int(value)) if value is not None else None

    async def set_dehumid_mode(self, dehumid_mode: VentDehumidMode):
        """Sets the dehumid mode"""
        await self._value_accessor.set_dehumid_mode(self, dehumid_mode)

    @property
    def bypass_mode(self) -> VentBypassMode | None:
        """Returns the bypass mode"""
        value = self._value_accessor.get_value(self, "bypassMode")
        return VentBypassMode(int(value)) if value is not None else None

    @property
    def bypass_state(self) -> VentBypassState | None:
        """Returns the bypass state"""
        value = self._value_accessor.get_value(self, "bypassState")
        return VentBypassState(int(value)) if value is not None else None

    async def set_bypass_state(self, bypass_state: VentBypassState):
        """Sets the bypass state"""
        await self._value_accessor.set_bypass_state(self, bypass_state)

    @property
    def working_mode(self) -> VentWorkingMode | VentWorkingModeZimmermann | None:
        """Returns the working mode"""
        value = self._value_accessor.get_value(self, "workingMode")
        if self.device_model in [
            VentDeviceModel.ZIMMERMANN_V1,
            VentDeviceModel.ZIMMERMANN_V2,
        ]:
            return VentWorkingModeZimmermann(int(value)) if value is not None else None
        else:
            return VentWorkingMode(int(value)) if value is not None else None

    async def set_working_mode(
        self, working_mode: VentWorkingMode | VentWorkingModeZimmermann
    ):
        """Sets the working mode"""
        await self._value_accessor.set_working_mode(self, working_mode)

    @property
    def sub_working_mode(
        self,
    ) -> VentSubWorkingMode | VentSubWorkingModeZimmermann | None:
        """Returns the mode"""
        value = self._value_accessor.get_value(self, "subWorkingMode")
        if self.device_model in [
            VentDeviceModel.ZIMMERMANN_V1,
            VentDeviceModel.ZIMMERMANN_V2,
        ]:
            return (
                VentSubWorkingModeZimmermann(int(value)) if value is not None else None
            )
        else:
            return VentSubWorkingMode(int(value)) if value is not None else None


class VentWorkingMode(IntEnum):
    """MyGekko Vent Working Mode"""

    AUTO = 0
    MANUAL = 1
    PLUGGIT_AUTO = 2
    PLUGGIT_WEEK = 3


class VentWorkingModeZimmermann(IntEnum):
    """MyGekko Vent Working Mode for Zimmermann"""

    OFF = 0
    ECO_SUMMER = 1
    ECO_WINTER = 2
    COMFORT = 3
    STOVE = 4


class VentSubWorkingMode(IntEnum):
    """MyGekko Vent SubWorkingMode"""

    EXHAUST = 0
    EXHAUST_SUPPLY = 1
    EXHAUST_SUPPLY_HEAT_RECOVERY = 2


class VentSubWorkingModeZimmermann(IntEnum):
    """MyGekko Vent SubWorkingMode for Zimmermann"""

    MIDDLE_TEMP_OFFSET = 0
    ONLY_OFFSET = 1


class VentWorkingLevel(IntEnum):
    """MyGekko Vent Working Level"""

    OFF = 0
    LEVEL_1 = 1
    LEVEL_2 = 2
    LEVEL_3 = 3
    LEVEL_4 = 4


class VentDeviceModel(IntEnum):
    """MyGekko Vent Device Model"""

    STANDARD = 0
    PLUGGIT = 1
    ZIMMERMANN_V1 = 2
    WESTAFLEX = 3
    STIEBEL_LWZ = 4
    ZIMMERMANN_V2 = 5


class VentFeature(IntEnum):
    """MyGekko Vent Features"""

    WORKING_LEVEL = 0
    CO2 = 1
    HUMIDITY = 2
    AIR_QUALITY = 3


class VentElementInfo(IntEnum):
    """MyGekko Vent ElementInfo"""

    OK = 0
    MANUAL_OFF = 1
    MANUAL_ON = 2
    LOCKED = 3
    ALARM = 4


class VentCoolingMode(IntEnum):
    """MyGekko Vent Cooling Mode"""

    OFF = 0
    ON = 1


class VentDehumidMode(IntEnum):
    """MyGekko Vent Dehumid Mode"""

    OFF = 0
    ON = 1


class VentBypassMode(IntEnum):
    """MyGekko Vent Bypass Mode"""

    AUTO = 0
    MANUAL = 1
    SUMMER = 2


class VentBypassState(IntEnum):
    """MyGekko Vent Bypass State"""

    AUTO = 0
    MANUAL = 1
    SUMMER = 2


class VentValueAccessor(EntityValueAccessor):
    """Vent value accessor"""

    def __init__(self, data_provider: DataProviderBase):
        super().__init__()
        self._data_provider = data_provider
        self._data_provider.subscribe(self)

    def update_status(self, status, hardware):
        if status is not None and "vents" in status:
            vents = status["vents"]
            for key in vents:
                if key.startswith("item"):
                    if key not in self._data:
                        self._data[key] = {}

                    if "sumstate" in vents[key] and "value" in vents[key]["sumstate"]:
                        self.read_value(key, vents[key]["sumstate"]["value"], hardware)

    def read_value(self, key, value, hardware):
        """Reads a value based on the given hardware."""
        if hardware == "legacy":
            (
                self._data[key]["workingLevel"],
                self._data[key]["deviceModel"],
                self._data[key]["workingMode"],
                self._data[key]["bypassState"],
                self._data[key]["maximumWorkingLevel"],
                self._data[key]["relativeHumidityLevel"],
                self._data[key]["co2Value"],
                self._data[key]["airQualityLevel"],
                self._data[key]["supplyAirTemperatureValue"],
                self._data[key]["exhaustAirTemperatureValue"],
                self._data[key]["outsideAirTemperatureValue"],
                self._data[key]["outgoingAirTemperatureValue"],
                self._data[key]["supplyAirWorkingLevel"],
                self._data[key]["exhaustAirWorkingLevel"],
                self._data[key]["elementInfo"],
                *_other,
            ) = value.split(
                ";",
            )
        else:
            (
                self._data[key]["workingLevel"],
                self._data[key]["deviceModel"],
                self._data[key]["workingMode"],
                self._data[key]["bypassState"],
                self._data[key]["maximumWorkingLevel"],
                self._data[key]["relativeHumidityLevel"],
                self._data[key]["airQualityLevel"],
                self._data[key]["co2Value"],
                self._data[key]["supplyAirTemperatureValue"],
                self._data[key]["exhaustAirTemperatureValue"],
                self._data[key]["outsideAirTemperatureValue"],
                self._data[key]["outgoingAirTemperatureValue"],
                self._data[key]["supplyAirWorkingLevel"],
                self._data[key]["exhaustAirWorkingLevel"],
                self._data[key]["elementInfo"],
                self._data[key]["subWorkingMode"],
                self._data[key]["coolingModeState"],
                self._data[key]["dehumidModeState"],
                self._data[key]["bypassMode"],
                *_other,
            ) = value.split(
                ";",
            )

    def update_resources(self, resources):
        if resources is not None and "vents" in resources:
            vents = resources["vents"]
            for key in vents:
                if key.startswith("item"):
                    if key not in self._data:
                        self._data[key] = {}
                    self._data[key]["name"] = vents[key]["name"]

    @property
    def vents(self):
        """Returns the vents read from MyGekko"""
        result: list[Vent] = []
        for key, data in self._data.items():
            if "name" not in data:
                continue
            result.append(Vent(key, data["name"], self))

        return result

    def get_features(self, vent: Vent) -> list[VentFeature]:
        """Returns the supported features of the given vent"""
        result = list()

        if vent and vent.entity_id:
            if vent.entity_id in self._data:
                data = self._data[vent.entity_id]
                if "workingLevel" in data and data["workingLevel"]:
                    result.append(VentFeature.WORKING_LEVEL)
                if "airQualityLevel" in data and data["airQualityLevel"]:
                    result.append(VentFeature.AIR_QUALITY)
                if "co2Value" in data and data["co2Value"]:
                    result.append(VentFeature.CO2)
                if "relativeHumidityLevel" in data and data["relativeHumidityLevel"]:
                    result.append(VentFeature.HUMIDITY)

        return result

    async def set_working_level(
        self, vent: Vent, working_level: VentWorkingLevel
    ) -> None:
        """Sets the working level, OFF is sent as -1"""
        await self._data_provider.write_data(
            vent.resource_path,
            str(working_level if working_level is not VentWorkingLevel.OFF else -1),
        )

    async def set_bypass_state(self, vent: Vent, bypass_state: VentBypassState) -> None:
        """Sets the bypass state"""
        if vent and vent.entity_id:
            await self._data_provider.write_data(
                vent.resource_path, "BY" + str(bypass_state)
            )

    async def set_cooling_mode(self, vent: Vent, cooling_mode: VentCoolingMode) -> None:
        """Sets the cooling mode"""
        if vent and vent.entity_id:
            await self._data_provider.write_data(
                vent.resource_path, "C" + str(cooling_mode)
            )

    async def set_dehumid_mode(self, vent: Vent, dehumid_mode: VentDehumidMode) -> None:
        """Sets the dehumid mode"""
        if vent and vent.entity_id:
            await self._data_provider.write_data(
                vent.resource_path, "D" + str(dehumid_mode)
            )

    async def set_working_mode(
        self,
        vent: Vent,
        working_mode: VentWorkingMode | VentWorkingModeZimmermann,
    ) -> None:
        """Sets the working mode"""
        if vent and vent.entity_id:
            await self._data_provider.write_data(
                vent.resource_path, "M" + str(working_mode)
            )
