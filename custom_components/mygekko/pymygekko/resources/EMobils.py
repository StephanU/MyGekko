"""MyGekko EMobils (charging stations) implementation"""
from __future__ import annotations

from enum import IntEnum

from ..data_provider import DataProviderBase
from ..data_provider import EntityValueAccessor
from . import Entity


class EMobil(Entity):
    """Class for MyGekko EMobil (charging station)"""

    def __init__(
        self, entity_id: str, name: str, value_accessor: EMobilValueAccessor
    ) -> None:
        super().__init__(entity_id, name, "/emobils/")
        self._value_accessor = value_accessor

    def _get_float(self, value_name: str) -> float | None:
        value = self._value_accessor.get_value(self, value_name)
        return float(value) if value is not None else None

    def _get_int(self, value_name: str) -> int | None:
        value = self._value_accessor.get_value(self, value_name)
        return int(value) if value is not None else None

    @property
    def plugged_state(self) -> EMobilPluggedState | None:
        """Returns whether a car is plugged in"""
        value = self._value_accessor.get_value(self, "pluggedState")
        return EMobilPluggedState(int(value)) if value is not None else None

    @property
    def charge_state(self) -> EMobilChargeState | None:
        """Returns the current charge state"""
        value = self._value_accessor.get_value(self, "chargeState")
        return EMobilChargeState(int(value)) if value is not None else None

    @property
    def charge_request_state(self) -> EMobilChargeRequestState | None:
        """Returns the current charge request state"""
        value = self._value_accessor.get_value(self, "chargeRequestState")
        return EMobilChargeRequestState(int(value)) if value is not None else None

    @property
    def current_charging_power(self) -> float | None:
        """Returns the current charging power in kW"""
        return self._get_float("currentChargingPowerValue")

    @property
    def maximum_charging_power(self) -> float | None:
        """Returns the maximum charging power in kW"""
        return self._get_float("maximumChargingPowerValue")

    @property
    def charging_power_setpoint(self) -> float | None:
        """Returns the charging power set point in kW"""
        return self._get_float("chargingPowerSetPointValue")

    @property
    def electric_current_setpoint(self) -> int | None:
        """Returns the electric current set point in Ampere"""
        return self._get_int("electricCurrentSetPointValue")

    @property
    def charge_user_name(self) -> str | None:
        """Returns the name of the charging user"""
        return self._value_accessor.get_value(self, "chargeUserName")

    @property
    def charge_duration_time(self) -> str | None:
        """Returns the charge duration time (hh:mm:ss)"""
        return self._value_accessor.get_value(self, "chargeDurationTime")

    @property
    def current_charging_energy(self) -> float | None:
        """Returns the current charging energy in kWh"""
        return self._get_float("currentChargingEnergyValue")

    @property
    def charge_start_time(self) -> str | None:
        """Returns the charge start time (hh:mm:ss)"""
        return self._value_accessor.get_value(self, "chargeStartTime")

    @property
    def charge_user_index(self) -> int | None:
        """Returns the index of the charging user"""
        return self._get_int("chargeUserIndex")

    async def start_charge(self):
        """Starts charging"""
        await self._value_accessor.start_charge(self)

    async def stop_charge(self):
        """Stops charging"""
        await self._value_accessor.stop_charge(self)

    async def set_charging_power_setpoint(self, power: float):
        """Sets the charging power set point in kW"""
        await self._value_accessor.set_charging_power_setpoint(self, power)


class EMobilPluggedState(IntEnum):
    """MyGekko EMobils Plugged State"""

    NOT_PLUGGED = 0
    PLUGGED = 1


class EMobilChargeState(IntEnum):
    """MyGekko EMobils Charge State"""

    OFF = 0
    ON = 1
    PAUSED = 2


class EMobilChargeRequestState(IntEnum):
    """MyGekko EMobils Charge Request State"""

    OFF = 0
    ON = 1


class EMobilValueAccessor(EntityValueAccessor):
    """EMobils value accessor"""

    SUM_STATE_FIELDS = [
        "pluggedState",
        "chargeState",
        "chargeRequestState",
        "currentChargingPowerValue",
        "maximumChargingPowerValue",
        "chargingPowerSetPointValue",
        "electricCurrentSetPointValue",
        "chargeUserName",
        "chargeDurationTime",
        "currentChargingEnergyValue",
        "elementInfo",
        "chargeStartTime",
        "chargeUserIndex",
    ]

    def __init__(self, data_provider: DataProviderBase):
        super().__init__()
        self._data_provider = data_provider
        data_provider.subscribe(self)

    def update_status(self, status, hardware):
        if status is not None and "emobils" in status:
            emobils = status["emobils"]
            for key in emobils:
                if key.startswith("item"):
                    if key not in self._data:
                        self._data[key] = {}

                    if (
                        "sumstate" in emobils[key]
                        and "value" in emobils[key]["sumstate"]
                    ):
                        values = emobils[key]["sumstate"]["value"].split(";")
                        for name, value in zip(self.SUM_STATE_FIELDS, values):
                            self._data[key][name] = value

    def update_resources(self, resources):
        if resources is not None and "emobils" in resources:
            emobils = resources["emobils"]
            for key in emobils:
                if key.startswith("item"):
                    if key not in self._data:
                        self._data[key] = {}
                    self._data[key]["name"] = emobils[key]["name"]

    @property
    def emobils(self):
        """Returns the emobils read from MyGekko"""
        result: list[EMobil] = []
        for key, data in self._data.items():
            if "name" not in data:
                continue
            result.append(EMobil(key, data["name"], self))

        return result

    async def start_charge(self, emobil: EMobil) -> None:
        """Starts charging"""
        if emobil and emobil.entity_id:
            await self._data_provider.write_data(emobil.resource_path, "1")

    async def stop_charge(self, emobil: EMobil) -> None:
        """Stops charging"""
        if emobil and emobil.entity_id:
            await self._data_provider.write_data(emobil.resource_path, "-1")

    async def set_charging_power_setpoint(self, emobil: EMobil, power: float) -> None:
        """Sets the charging power set point in kW"""
        if emobil and emobil.entity_id:
            await self._data_provider.write_data(
                emobil.resource_path, "CS" + str(power)
            )
