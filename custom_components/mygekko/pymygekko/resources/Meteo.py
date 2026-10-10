"""MyGekko Meteos implementation"""
from __future__ import annotations

import logging
from typing import Any

from ..data_provider import DataProviderBase
from ..data_provider import EntityValueAccessor
from . import ReadOnlyEntity

_LOGGER: logging.Logger = logging.getLogger(__name__)


class Meteo(ReadOnlyEntity):
    """Class for MyGekko Meteo"""

    def __init__(
        self, entity_id: str, name: str, value_accessor: MeteoValueAccessor
    ) -> None:
        super().__init__(entity_id, name)
        self._value_accessor = value_accessor

    @property
    def sensor_data(self) -> dict[str, Any]:
        """Returns the sensor data"""
        return self._value_accessor.get_data(self)


class MeteoValueAccessor(EntityValueAccessor):
    """Meteo value accessor"""

    def __init__(self, data_provider: DataProviderBase):
        super().__init__()
        self._data_provider = data_provider
        self._data_provider.subscribe(self)

    def update_status(self, status, hardware):
        meteo = status.get("globals", {}).get("meteo", {})
        for key, value in meteo.items():
            if "value" in value:
                self._data[key] = value["value"]
            else:
                self._data.setdefault(key, {})

    def update_resources(self, resources):
        """Nothing to do here since Meteo data is in status and no additional resources are available"""

    @property
    def meteo(self):
        """Returns the meteo read from MyGekko"""
        return Meteo("meteo", "Weather", self)

    def get_data(self, meteo: Meteo) -> dict[str, Any]:
        """Returns the data of the given meteo"""
        return self._data
