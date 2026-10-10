"""MyGekko Cams implementation"""
from __future__ import annotations

from enum import IntEnum

from ..data_provider import DataProviderBase
from ..data_provider import EntityValueAccessor
from . import Entity


class Cam(Entity):
    """Class for MyGekko Cam"""

    def __init__(
        self, entity_id: str, name: str, value_accessor: CamValueAccessor
    ) -> None:
        super().__init__(entity_id, name, "/cams/")
        self._value_accessor = value_accessor
        self._supported_features = self._value_accessor.get_features(self)

    @property
    def supported_features(self) -> list[CamFeature]:
        """Returns the supported features"""
        return self._supported_features

    @property
    def image_url(self) -> str | None:
        """Returns the image url"""
        return self._value_accessor.get_value(self, "imagepath")

    @property
    def stream_url(self) -> str | None:
        """Returns the stream url"""
        return self._value_accessor.get_value(self, "streampath")


class CamNewRecordAvailableState(IntEnum):
    """MyGekko Cams Record Available State"""

    NO = 0
    YES = 1


class CamFeature(IntEnum):
    """MyGekko Cams Feature"""

    ON_OFF = 0
    STREAM = 1


class CamValueAccessor(EntityValueAccessor):
    """Cam value accessor"""

    def __init__(self, data_provider: DataProviderBase):
        super().__init__()
        self._data_provider = data_provider
        self._data_provider.subscribe(self)

    def update_status(self, status, hardware):
        if status is not None and "cams" in status:
            cams = status["cams"]
            for key in cams:
                if key.startswith("item"):
                    if key not in self._data:
                        self._data[key] = {}

                    if "sumstate" in cams[key] and "value" in cams[key]["sumstate"]:
                        (
                            self._data[key]["newRecordsAvailableState"],
                            *_other,
                        ) = cams[
                            key
                        ]["sumstate"]["value"].split(
                            ";",
                        )

    def update_resources(self, resources):
        if resources is not None and "cams" in resources:
            cams = resources["cams"]
            for key in cams:
                if key.startswith("item"):
                    if key not in self._data:
                        self._data[key] = {}
                    self._data[key]["name"] = cams[key]["name"]
                    self._data[key]["imagepath"] = cams[key].get("imagepath", None)
                    self._data[key]["streampath"] = cams[key].get("streampath", None)

    @property
    def cams(self):
        """Returns the cams read from MyGekko"""
        result: list[Cam] = []
        for key, data in self._data.items():
            if "name" not in data:
                continue
            result.append(Cam(key, data["name"], self))

        return result

    def get_features(self, cam: Cam) -> list[CamFeature]:
        """Returns the supported features"""
        result = list()

        if cam and cam.entity_id:
            if cam.entity_id in self._data:
                data = self._data[cam.entity_id]
                if "streampath" in data and data["streampath"]:
                    result.append(CamFeature.STREAM)

        return result
