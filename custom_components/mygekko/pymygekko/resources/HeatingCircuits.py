"""MyGekko HeatingCircuits implementation"""
from __future__ import annotations

from enum import IntEnum

from ..data_provider import DataProviderBase
from ..data_provider import EntityValueAccessor
from . import Entity


class HeatingCircuit(Entity):
    """Class for MyGekko HeatingCircuit"""

    def __init__(
        self, entity_id: str, name: str, value_accessor: HeatingCircuitValueAccessor
    ) -> None:
        super().__init__(entity_id, name, "/heatingcircuits/")
        self._value_accessor = value_accessor

    @property
    def device_model(self) -> HeatingCircuitDeviceModel | None:
        """Returns the device model"""
        value = self._value_accessor.get_value(self, "deviceModel")
        return HeatingCircuitDeviceModel(int(value)) if value is not None else None

    @property
    def flow_temperature(self) -> float | None:
        """Returns the current flow temperature"""
        value = self._value_accessor.get_value(self, "flowTemperatureValue")
        return float(value) if value is not None else None

    @property
    def return_flow_temperature(self) -> float | None:
        """Returns the current return flow temperature"""
        value = self._value_accessor.get_value(self, "returnFlowTemperatureValue")
        return float(value) if value is not None else None

    @property
    def dew_point(self) -> float | None:
        """Returns the current dew point"""
        value = self._value_accessor.get_value(self, "dewPointValue")
        return float(value) if value is not None else None

    @property
    def pump_working_level(self) -> float | None:
        """Returns the current pump working level in percent"""
        value = self._value_accessor.get_value(self, "pumpWorkingLevel")
        return float(value) if value is not None else None

    @property
    def cooling_mode_state(self) -> HeatingCircuitCoolingModeState | None:
        """Returns the current cooling mode state"""
        value = self._value_accessor.get_value(self, "coolingModeState")
        return HeatingCircuitCoolingModeState(int(value)) if value is not None else None

    @property
    def flow_temperature_setpoint(self) -> float | None:
        """Returns the flow temperature set point"""
        value = self._value_accessor.get_value(self, "flowTemperatureSetPointValue")
        return float(value) if value is not None else None

    @property
    def valve_opening_level(self) -> float | None:
        """Returns the current valve opening level in percent"""
        value = self._value_accessor.get_value(self, "valveOpeningLevel")
        return float(value) if value is not None else None

    @property
    def state(self) -> HeatingCircuitState | None:
        """Returns the current state"""
        value = self._value_accessor.get_value(self, "currentState")
        return HeatingCircuitState(int(value)) if value is not None else None


class HeatingCircuitDeviceModel(IntEnum):
    """MyGekko HeatingCircuits Device Model"""

    INDIVIDUAL = 0
    BUDERUS = 1
    STIEBEL = 2
    VAILLANT = 3


class HeatingCircuitCoolingModeState(IntEnum):
    """MyGekko HeatingCircuits Cooling Mode State"""

    OFF = 0
    ON = 1


class HeatingCircuitState(IntEnum):
    """MyGekko HeatingCircuits State"""

    OFF = 0
    ON = 1
    AUTO = 2


class HeatingCircuitValueAccessor(EntityValueAccessor):
    """HeatingCircuits value accessor"""

    SUM_STATE_FIELDS = [
        "deviceModel",
        "flowTemperatureValue",
        "returnFlowTemperatureValue",
        "dewPointValue",
        "pumpWorkingLevel",
        "coolingModeState",
        "flowTemperatureSetPointValue",
        "valveOpeningLevel",
        "elementInfo",
        "currentState",
    ]

    def __init__(self, data_provider: DataProviderBase):
        super().__init__()
        self._data_provider = data_provider
        data_provider.subscribe(self)

    def update_status(self, status, hardware):
        if status is not None and "heatingcircuits" in status:
            heating_circuits = status["heatingcircuits"]
            for key in heating_circuits:
                if key.startswith("item"):
                    if key not in self._data:
                        self._data[key] = {}

                    if (
                        "sumstate" in heating_circuits[key]
                        and "value" in heating_circuits[key]["sumstate"]
                    ):
                        values = heating_circuits[key]["sumstate"]["value"].split(";")
                        for name, value in zip(self.SUM_STATE_FIELDS, values):
                            self._data[key][name] = value

    def update_resources(self, resources):
        if resources is not None and "heatingcircuits" in resources:
            heating_circuits = resources["heatingcircuits"]
            for key in heating_circuits:
                if key.startswith("item"):
                    if key not in self._data:
                        self._data[key] = {}
                    self._data[key]["name"] = heating_circuits[key]["name"]

    @property
    def heating_circuits(self):
        """Returns the heating circuits read from MyGekko"""
        result: list[HeatingCircuit] = []
        for key, data in self._data.items():
            if "name" not in data:
                continue
            result.append(HeatingCircuit(key, data["name"], self))

        return result
