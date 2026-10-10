"""MyGekko Actions implementation"""
from __future__ import annotations

from enum import IntEnum

from ..data_provider import DataProviderBase
from ..data_provider import EntityValueAccessor
from . import Entity


class Action(Entity):
    """Class for MyGekko Action"""

    def __init__(
        self, entity_id: str, name: str, value_accessor: ActionValueAccessor
    ) -> None:
        super().__init__(entity_id, name, "/actions/")
        self._value_accessor = value_accessor
        self._supported_features = self._value_accessor.get_features(self)

    @property
    def supported_features(self) -> list[ActionFeature]:
        """Returns the supported features"""
        return self._supported_features

    @property
    def state(self) -> ActionState | None:
        """Returns the current action state"""
        value = self._value_accessor.get_value(self, "currentState")
        return ActionState(int(value)) if value is not None else None

    async def set_state(self, state: ActionState):
        """Sets the action state"""
        await self._value_accessor.set_state(self, state)

    @property
    def start_condition_state(self) -> ActionState | None:
        """Returns the start condition state"""
        value = self._value_accessor.get_value(self, "startConditionState")
        return ActionState(int(value)) if value is not None else None


class ActionState(IntEnum):
    """MyGekko Action State"""

    OFF = 0
    ON = 1


class ActionFeature(IntEnum):
    """MyGekko Action Features"""

    ON_OFF = 0


class ActionValueAccessor(EntityValueAccessor):
    """Action value accessor"""

    def __init__(self, data_provider: DataProviderBase):
        super().__init__()
        self._data_provider = data_provider
        data_provider.subscribe(self)

    def update_status(self, status, hardware):
        if status is not None and "actions" in status:
            actions = status["actions"]
            for key in actions:
                if key.startswith("item"):
                    if key not in self._data:
                        self._data[key] = {}

                    if (
                        "sumstate" in actions[key]
                        and "value" in actions[key]["sumstate"]
                    ):
                        self.read_value(
                            key, actions[key]["sumstate"]["value"], hardware
                        )

    def read_value(self, key, value, hardware):
        """Reads a value based on the given hardware."""
        if hardware == "legacy":
            (
                self._data[key]["currentState"],
                self._data[key]["elementInfo"],
            ) = value.split(";")
        else:
            (
                self._data[key]["currentState"],
                self._data[key]["startConditionState"],
                self._data[key]["elementInfo"],
                *_other,
            ) = value.split(";")

    def update_resources(self, resources):
        if resources is not None and "actions" in resources:
            actions = resources["actions"]
            for key in actions:
                if key.startswith("item"):
                    if key not in self._data:
                        self._data[key] = {}
                    self._data[key]["name"] = actions[key]["name"]

    @property
    def actions(self):
        """Returns the actions read from MyGekko"""
        result: list[Action] = []
        for key, data in self._data.items():
            if "name" not in data:
                continue
            result.append(Action(key, data["name"], self))

        return result

    def get_features(self, action: Action) -> list[ActionFeature]:
        """Returns the supported features"""
        result = list()

        if action and action.entity_id:
            if action.entity_id in self._data:
                data = self._data[action.entity_id]
                if "currentState" in data and data["currentState"]:
                    result.append(ActionFeature.ON_OFF)

        return result

    async def set_state(self, action: Action, state: ActionState) -> None:
        """Sets the state"""
        if action and action.entity_id:
            await self._data_provider.write_data(action.resource_path, str(state))
