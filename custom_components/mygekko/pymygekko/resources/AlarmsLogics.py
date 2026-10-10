"""MyGekko AlarmsLogics implementation"""
from __future__ import annotations

from ..data_provider import DataProviderBase
from ..data_provider import EntityValueAccessor
from . import Entity


class AlarmsLogic(Entity):
    """Class for MyGekko AlarmsLogic"""

    def __init__(
        self, entity_id: str, name: str, value_accessor: AlarmsLogicValueAccessor
    ) -> None:
        super().__init__(entity_id, name, "/alarms_logics/")
        self._value_accessor = value_accessor

    @property
    def value(self) -> float | None:
        """Returns the value"""
        value = self._value_accessor.get_value(self, "currentValue")
        return float(value) if value is not None else None


class AlarmsLogicValueAccessor(EntityValueAccessor):
    """AlarmsLogic value accessor"""

    def __init__(self, data_provider: DataProviderBase):
        super().__init__()
        self._data_provider = data_provider
        data_provider.subscribe(self)

    def update_status(self, status, hardware):
        if status is not None and "alarms_logics" in status:
            alarms_logics = status["alarms_logics"]
            for key in alarms_logics:
                if key.startswith("item"):
                    if key not in self._data:
                        self._data[key] = {}

                    if (
                        "sumstate" in alarms_logics[key]
                        and "value" in alarms_logics[key]["sumstate"]
                    ):
                        (
                            self._data[key]["currentValue"],
                            *_other,
                        ) = alarms_logics[
                            key
                        ]["sumstate"]["value"].split(";")

    def update_resources(self, resources):
        if resources is not None and "alarms_logics" in resources:
            alarms_logics = resources["alarms_logics"]
            for key in alarms_logics:
                if key.startswith("item"):
                    if key not in self._data:
                        self._data[key] = {}
                    self._data[key]["name"] = alarms_logics[key]["name"]

    @property
    def alarms_logics(self):
        """Returns the alarmsLogics read from MyGekko"""
        result: list[AlarmsLogic] = []
        for key, data in self._data.items():
            if "name" not in data:
                continue
            result.append(AlarmsLogic(key, data["name"], self))

        return result
