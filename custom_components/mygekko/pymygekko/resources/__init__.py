# SPDX-FileCopyrightText: 2023-present Stephan Uhle <stephanu@gmx.net>
#
# SPDX-License-Identifier: MIT


class ReadOnlyEntity:
    """Base class for read only MyGekko entities"""

    def __init__(self, entity_id: str, name: str) -> None:
        self.entity_id = entity_id
        self.name = name


class Entity(ReadOnlyEntity):
    """Base class for MyGekko entities"""

    def __init__(self, entity_id: str, name: str, resource_path_prefix: str) -> None:
        super().__init__(entity_id, name)
        self._resource_path = resource_path_prefix + self.entity_id

    @property
    def resource_path(self) -> str:
        """Returns the resource path of this entity"""
        return self._resource_path
