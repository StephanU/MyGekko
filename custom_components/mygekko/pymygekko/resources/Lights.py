"""MyGekko Lights implementation"""
from __future__ import annotations

from enum import IntEnum
from math import ceil

from ..data_provider import DataProviderBase
from ..data_provider import EntityValueAccessor
from . import Entity


class Light(Entity):
    """Class for MyGekko Light"""

    def __init__(
        self, entity_id: str, name: str, value_accessor: LightValueAccessor
    ) -> None:
        super().__init__(entity_id, name, "/lights/")
        self._value_accessor = value_accessor
        self._supported_features = self._value_accessor.get_features(self)

    @property
    def supported_features(self) -> list[LightFeature]:
        """Returns the supported features"""
        return self._supported_features

    @property
    def state(self) -> LightState | None:
        """Returns the current state"""
        value = self._value_accessor.get_value(self, "currentState")
        return LightState(int(value)) if value is not None else None

    async def set_state(self, state: LightState):
        """Sets the state"""
        await self._value_accessor.set_state(self, state)

    @property
    def brightness(self) -> int | None:
        """Returns the current brightness"""
        value = self._value_accessor.get_value(self, "dimLevel")
        return ceil(float(value)) if value is not None else None

    async def set_brightness(self, brightness: int):
        """Sets the brightness"""
        await self._value_accessor.set_brightness(self, brightness)

    @property
    def rgb_color(self) -> tuple[int, int, int] | None:
        """Returns the current rgb color"""
        value = self._value_accessor.get_value(self, "rgbColor")
        return ColorUtilities.decimal_to_rgb(int(value)) if value is not None else None

    async def set_rgb_color(self, rgb_color: tuple[int, int, int]):
        """Sets the rgb value"""
        await self._value_accessor.set_rgb_color(self, rgb_color)


class LightState(IntEnum):
    """MyGekko Lights State"""

    OFF = 0
    ON = 1


class LightFeature(IntEnum):
    """MyGekko Lights Feature"""

    ON_OFF = 0
    DIMMABLE = 1
    RGB_COLOR = 2


class LightValueAccessor(EntityValueAccessor):
    """Lights value accessor"""

    def __init__(self, data_provider: DataProviderBase):
        super().__init__()
        self._data_provider = data_provider
        data_provider.subscribe(self)

    def update_status(self, status, hardware):
        if status is not None and "lights" in status:
            lights = status["lights"]
            for key in lights:
                if key.startswith("item"):
                    if key not in self._data:
                        self._data[key] = {}

                    if "sumstate" in lights[key] and "value" in lights[key]["sumstate"]:
                        (
                            self._data[key]["currentState"],
                            self._data[key]["dimLevel"],
                            self._data[key]["rgbColor"],
                            self._data[key]["tunableWhiteLevel"],
                            self._data[key]["elementInfo"],
                            *_other,
                        ) = lights[key]["sumstate"]["value"].split(";")

                if key.startswith("group"):
                    if key not in self._data:
                        self._data[key] = {}

                    if "sumstate" in lights[key] and "value" in lights[key]["sumstate"]:
                        (
                            self._data[key]["currentState"],
                            *_other,
                        ) = lights[key][
                            "sumstate"
                        ]["value"].split(
                            ";",
                        )

    def update_resources(self, resources):
        if resources is not None and "lights" in resources:
            lights = resources["lights"]
            for key in lights:
                if key.startswith("item"):
                    if key not in self._data:
                        self._data[key] = {}
                    self._data[key]["name"] = lights[key]["name"]

                if key.startswith("group"):
                    if key not in self._data:
                        self._data[key] = {}
                    self._data[key]["name"] = lights[key]["name"]

    @property
    def lights(self):
        """Returns the lights read from MyGekko"""
        result: list[Light] = []
        for key, data in self._data.items():
            if "name" not in data:
                continue
            result.append(Light(key, data["name"], self))

        return result

    def get_features(self, light: Light) -> list[LightFeature]:
        """Returns the supported features"""
        result = list()

        if light and light.entity_id:
            if light.entity_id in self._data:
                data = self._data[light.entity_id]

                if light.entity_id.startswith("group"):
                    # on/off feature is the only feature for groups
                    result.append(LightFeature.ON_OFF)
                    return result

                if "currentState" in data and data["currentState"]:
                    result.append(LightFeature.ON_OFF)

                if "dimLevel" in data and data["dimLevel"]:
                    result.append(LightFeature.DIMMABLE)

                if "rgbColor" in data and data["rgbColor"]:
                    result.append(LightFeature.RGB_COLOR)

        return result

    async def set_state(self, light: Light, state: LightState) -> None:
        """Sets the state"""
        if light and light.entity_id:
            await self._data_provider.write_data(light.resource_path, str(state))

    async def set_brightness(self, light: Light, brightness: int) -> None:
        """Sets the brightness"""
        if light and light.entity_id and brightness >= 0 and brightness <= 100:
            await self._data_provider.write_data(
                light.resource_path, "D" + str(brightness)
            )

    async def set_rgb_color(
        self, light: Light, rgb_color: tuple[int, int, int]
    ) -> None:
        """Sets the rgb value"""
        if (
            light
            and light.entity_id
            and rgb_color[0] >= 0
            and rgb_color[0] <= 255
            and rgb_color[1] >= 0
            and rgb_color[1] <= 255
            and rgb_color[2] >= 0
            and rgb_color[2] <= 255
        ):
            decimal_rbg_color = (
                (rgb_color[0] << 16) + (rgb_color[1] << 8) + rgb_color[2]
            )
            await self._data_provider.write_data(
                light.resource_path, "C" + str(decimal_rbg_color)
            )


class ColorUtilities:
    """Color Utility class"""

    @staticmethod
    def decimal_to_rgb(decimal_rgb_color: int) -> tuple[int, int, int]:
        """Converts a decimal color representation to a rgb tuple"""
        return (
            (decimal_rgb_color >> 16) & 255,
            (decimal_rgb_color >> 8) & 255,
            decimal_rgb_color & 255,
        )
