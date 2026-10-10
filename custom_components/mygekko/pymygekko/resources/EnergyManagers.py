"""MyGekko EnergyManager implementation"""
from __future__ import annotations

from enum import IntEnum

from ..data_provider import DataProviderBase
from ..data_provider import EntityValueAccessor
from . import Entity


class EnergyManager(Entity):
    """Class for MyGekko EnergyManager"""

    def __init__(
        self, entity_id: str, name: str, value_accessor: EnergyManagerValueAccessor
    ) -> None:
        super().__init__(entity_id, name, "/energymanager/")
        self._value_accessor = value_accessor

    def _get_float(self, value_name: str) -> float | None:
        value = self._value_accessor.get_value(self, value_name)
        return float(value) if value is not None else None

    def _get_state(self, value_name: str, state_enum):
        value = self._value_accessor.get_value(self, value_name)
        return state_enum(int(value)) if value is not None else None

    @property
    def grid_meter_state(self) -> EnergyManagerComponentState | None:
        """Returns whether the grid meter is active"""
        return self._get_state("gridMeterState", EnergyManagerComponentState)

    @property
    def solar_panel_state(self) -> EnergyManagerComponentState | None:
        """Returns whether the solar panels are active"""
        return self._get_state("solarPanelState", EnergyManagerComponentState)

    @property
    def battery_state(self) -> EnergyManagerComponentState | None:
        """Returns whether the battery is active"""
        return self._get_state("batteryState", EnergyManagerComponentState)

    @property
    def grid_meter_power(self) -> float | None:
        """Returns the current grid meter power in Watt"""
        return self._get_float("gridMeterCurrentPowerValue")

    @property
    def power_exported_to_grid(self) -> float | None:
        """Returns the current power exported to the grid in Watt"""
        return self._get_float("currentPowerExportedToGridValue")

    @property
    def power_from_solar_panels(self) -> float | None:
        """Returns the current power from the solar panels in Watt"""
        return self._get_float("currentPowerFromSolarPanelsValue")

    @property
    def power_from_battery(self) -> float | None:
        """Returns the current power from the battery in Watt"""
        return self._get_float("currentPowerFromBatteryValue")

    @property
    def power_charging_battery(self) -> float | None:
        """Returns the current power charging the battery in Watt"""
        return self._get_float("currentPowerChargingBatteryValue")

    @property
    def home_power_consumption(self) -> float | None:
        """Returns the current home power consumption in Watt"""
        return self._get_float("currentHomePowerConsumptionValue")

    @property
    def alternative_power_consumption(self) -> float | None:
        """Returns the current alternative power consumption in Watt"""
        return self._get_float("currentAlternativePowerConsupmtionValue")

    @property
    def daily_energy_imported_from_grid(self) -> float | None:
        """Returns the total daily energy imported from the grid in Wh"""
        return self._get_float("totalDailyImportedEnergyFromGridValue")

    @property
    def daily_energy_exported_to_grid(self) -> float | None:
        """Returns the total daily energy exported to the grid in Wh"""
        return self._get_float("totalDailyExportedEnergyToGridValue")

    @property
    def daily_energy_from_solar_panels(self) -> float | None:
        """Returns the total daily energy from the solar panels in Wh"""
        return self._get_float("totalDailyEnergyFromSolarPanelsValue")

    @property
    def daily_energy_from_battery(self) -> float | None:
        """Returns the total daily energy from the battery in Wh"""
        return self._get_float("totalDailyEnergyFromBatteryValue")

    @property
    def daily_energy_charging_battery(self) -> float | None:
        """Returns the total daily energy charging the battery in Wh"""
        return self._get_float("totalDailyEneryChargingBatteryValue")

    @property
    def daily_home_energy_consumption(self) -> float | None:
        """Returns the total daily home energy consumption in Wh"""
        return self._get_float("totalDailyHomeEnergyConsumptionValue")

    @property
    def load_shedding_state(self) -> EnergyManagerState | None:
        """Returns the load shedding state"""
        return self._get_state("loadSheddingState", EnergyManagerState)

    @property
    def ems_state(self) -> EnergyManagerState | None:
        """Returns the energy management system state"""
        return self._get_state("EMSState", EnergyManagerState)

    @property
    def battery_model(self) -> EnergyManagerBatteryModel | None:
        """Returns the battery model"""
        return self._get_state("batteryModel", EnergyManagerBatteryModel)

    @property
    def battery_soc(self) -> float | None:
        """Returns the battery state of charge in percent"""
        return self._get_float("batterySoCLevel")

    @property
    def ems_enabled(self) -> EnergyManagerEmsEnabled | None:
        """Returns whether the energy management system is enabled"""
        return self._get_state("EMSEnabled", EnergyManagerEmsEnabled)

    @property
    def max_power_consumption_from_grid(self) -> float | None:
        """Returns the maximum power consumption from the grid in kW"""
        return self._get_float("maximumPowerConsumptionFromGridValue")

    @property
    def max_power_export_to_grid(self) -> float | None:
        """Returns the maximum power export to the grid in kW"""
        return self._get_float("maximumPowerExportToGridValue")

    @property
    def max_power_solar_panels(self) -> float | None:
        """Returns the maximum power of the solar panels in kW"""
        return self._get_float("maximumPowerSolarPanelsValue")

    @property
    def max_power_battery(self) -> float | None:
        """Returns the maximum power of the battery in kW"""
        return self._get_float("maximumPowerBatteryValue")


class EnergyManagerComponentState(IntEnum):
    """MyGekko EnergyManager Component State"""

    NOT_ACTIVE = 0
    ACTIVE = 1


class EnergyManagerState(IntEnum):
    """MyGekko EnergyManager On/Off State"""

    OFF = 0
    ON = 1


class EnergyManagerEmsEnabled(IntEnum):
    """MyGekko EnergyManager EMS Enabled State"""

    DISABLED = 0
    ENABLED = 1


class EnergyManagerBatteryModel(IntEnum):
    """MyGekko EnergyManager Battery Model"""

    UNAVAILABLE = 0
    E3DC_S10 = 1
    BYD = 2
    VARTA_STORAGE = 3
    INDIVIDUAL = 4
    BY_SUN_SPEC_INVERTERS = 5


class EnergyManagerValueAccessor(EntityValueAccessor):
    """EnergyManager value accessor"""

    SUM_STATE_FIELDS = [
        "elementInfo",
        "gridMeterState",
        "solarPanelState",
        "batteryState",
        "gridMeterCurrentPowerValue",
        "currentPowerExportedToGridValue",
        "currentPowerFromSolarPanelsValue",
        "currentPowerFromBatteryValue",
        "currentPowerChargingBatteryValue",
        "currentHomePowerConsumptionValue",
        "currentAlternativePowerConsupmtionValue",
        "totalDailyImportedEnergyFromGridValue",
        "totalDailyExportedEnergyToGridValue",
        "totalDailyEnergyFromSolarPanelsValue",
        "totalDailyEnergyFromBatteryValue",
        "totalDailyEneryChargingBatteryValue",
        "totalDailyHomeEnergyConsumptionValue",
        "loadSheddingState",
        "EMSState",
        "batteryModel",
        "batterySoCLevel",
        "EMSEnabled",
        "maximumPowerConsumptionFromGridValue",
        "maximumPowerExportToGridValue",
        "maximumPowerSolarPanelsValue",
        "maximumPowerBatteryValue",
    ]

    def __init__(self, data_provider: DataProviderBase):
        super().__init__()
        self._data_provider = data_provider
        data_provider.subscribe(self)

    def update_status(self, status, hardware):
        if status is not None and "energymanager" in status:
            energy_managers = status["energymanager"]
            for key in energy_managers:
                if key.startswith("item"):
                    if key not in self._data:
                        self._data[key] = {}

                    if (
                        "sumstate" in energy_managers[key]
                        and "value" in energy_managers[key]["sumstate"]
                    ):
                        values = energy_managers[key]["sumstate"]["value"].split(";")
                        for name, value in zip(self.SUM_STATE_FIELDS, values):
                            self._data[key][name] = value

    def update_resources(self, resources):
        if resources is not None and "energymanager" in resources:
            energy_managers = resources["energymanager"]
            for key in energy_managers:
                if key.startswith("item"):
                    if key not in self._data:
                        self._data[key] = {}
                    self._data[key]["name"] = energy_managers[key]["name"]

    @property
    def energy_managers(self):
        """Returns the energy managers read from MyGekko"""
        result: list[EnergyManager] = []
        for key, data in self._data.items():
            if "name" not in data:
                continue
            result.append(EnergyManager(key, data["name"], self))

        return result
