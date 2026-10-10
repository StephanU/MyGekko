"""Clients for the MyGekko API (cloud query API, local API and demo mode)."""
from __future__ import annotations

import asyncio
import json
import logging
import pkgutil
import time
from typing import Any

from aiohttp import ClientError
from aiohttp import ClientSession
from aiohttp import ClientTimeout
from yarl import URL

from .errors import MyGekkoError
from .errors import MyGekkoTooManyRequests
from .errors import error_for_status
from .models import AccessDoor
from .models import AlarmSystem
from .models import HeatingSystem
from .models import MultiRoom
from .models import SmsEmail
from .models import Trend
from .models import Action
from .models import AlarmsLogic
from .models import Blind
from .models import Cam
from .models import Clock
from .models import Device
from .models import DoorInterCom
from .models import EMobil
from .models import EnergyCost
from .models import EnergyManager
from .models import HeatingCircuit
from .models import HotWaterSystem
from .models import Light
from .models import Load
from .models import Meteo
from .models import RoomTemp
from .models import Vent
from .store import ResourceStore

_LOGGER: logging.Logger = logging.getLogger(__name__)

API_PATH = "/api/v1/var"
CLOUD_HOST = "live.my-gekko.com"

# Every request is bound by this timeout, a hanging device must never block polling.
REQUEST_TIMEOUT = ClientTimeout(total=15, sock_connect=8)
# Names and URLs of the devices rarely change, so they are not read on every poll.
RESOURCES_REFRESH_SECONDS = 30 * 60
RESOURCES_RETRY_SECONDS = 60


class MyGekkoClient:
    """Base client: reads the documents of MyGekko and exposes the devices."""

    def __init__(self) -> None:
        """Initialize the client."""
        self.store = ResourceStore()
        self._resources_read_at: float | None = None
        # devices that stay unnamed even after reading the resources
        self._unnamed: set[tuple[str, str]] = set()

    # --- transport, implemented by the subclasses ---------------------------------

    async def _fetch_resources(self) -> dict:
        raise NotImplementedError

    async def _fetch_status(self) -> dict:
        raise NotImplementedError

    async def write(self, resource_path: str, value: str) -> None:
        """Send a command to a resource."""
        raise NotImplementedError

    async def try_connect(self) -> None:
        """Check that MyGekko can be reached with the given credentials."""
        await self._fetch_status()

    # --- reading ------------------------------------------------------------------

    async def read_data(self) -> None:
        """Read the current values (and, when needed, the device names)."""
        status = await self._fetch_status()
        resources = None
        if self._resources_outdated(status):
            try:
                resources = await self._fetch_resources()
            except MyGekkoTooManyRequests:
                raise
            except (MyGekkoError, TimeoutError, ClientError) as err:
                if self._resources_read_at is None:
                    raise
                # the names are known already, the valid status is still used
                _LOGGER.warning("Refreshing the device names failed: %s", err)
                self._resources_read_at = (
                    time.monotonic() - RESOURCES_REFRESH_SECONDS + RESOURCES_RETRY_SECONDS
                )

        # publish only after everything was read successfully
        if resources is not None:
            self.store.update_resources(resources)
            self._resources_read_at = time.monotonic()
            self._unnamed = self.store.unnamed_keys(status)
        self.store.update_status(status)

    def _resources_outdated(self, status: dict) -> bool:
        if self._resources_read_at is None:
            return True
        if time.monotonic() - self._resources_read_at > RESOURCES_REFRESH_SECONDS:
            return True
        # a device appeared that has no name and was not already unnamed before
        return bool(self.store.unnamed_keys(status) - self._unnamed)

    # --- devices ------------------------------------------------------------------

    def _devices(self, device_class: type[Device]) -> list[Any]:
        return [
            device_class(self, key, data["name"])
            for key, data in self.store.devices(device_class.SPEC).items()
        ]

    def get_globals_network(self) -> dict[str, str] | None:
        """Return the network information of the controller, None before the first read."""
        return self.store.globals_network or None

    def get_access_doors(self) -> list[AccessDoor]:
        """Return the access doors."""
        return self._devices(AccessDoor)

    def get_actions(self) -> list[Action]:
        """Return the actions."""
        return self._devices(Action)

    def get_alarms_logics(self) -> list[AlarmsLogic]:
        """Return the alarms and logics."""
        return self._devices(AlarmsLogic)

    def get_blinds(self) -> list[Blind]:
        """Return the blinds."""
        return self._devices(Blind)

    def get_cams(self) -> list[Cam]:
        """Return the cameras."""
        return self._devices(Cam)

    def get_clocks(self) -> list[Clock]:
        """Return the clocks (time switches)."""
        return self._devices(Clock)

    def get_door_inter_coms(self) -> list[DoorInterCom]:
        """Return the door intercoms."""
        return self._devices(DoorInterCom)

    def get_emobils(self) -> list[EMobil]:
        """Return the e-mobility charging stations."""
        return self._devices(EMobil)

    def get_energy_costs(self) -> list[EnergyCost]:
        """Return the energy meters."""
        return self._devices(EnergyCost)

    def get_energy_managers(self) -> list[EnergyManager]:
        """Return the energy managers."""
        return self._devices(EnergyManager)

    def get_heating_circuits(self) -> list[HeatingCircuit]:
        """Return the heating circuits."""
        return self._devices(HeatingCircuit)

    def get_hot_water_systems(self) -> list[HotWaterSystem]:
        """Return the hot water systems."""
        return self._devices(HotWaterSystem)

    def get_lights(self) -> list[Light]:
        """Return the lights."""
        return self._devices(Light)

    def get_loads(self) -> list[Load]:
        """Return the loads."""
        return self._devices(Load)

    def get_meteo(self) -> Meteo:
        """Return the weather station."""
        return Meteo(self)

    def get_room_temps(self) -> list[RoomTemp]:
        """Return the room temperature controllers."""
        return self._devices(RoomTemp)

    def get_heating_systems(self) -> list[HeatingSystem]:
        """Return the heating systems."""
        return self._devices(HeatingSystem)

    def get_alarm_systems(self) -> list[AlarmSystem]:
        """Return the alarm systems."""
        return self._devices(AlarmSystem)

    def get_multirooms(self) -> list[MultiRoom]:
        """Return the multiroom audio players."""
        return self._devices(MultiRoom)

    def get_sms_emails(self) -> list[SmsEmail]:
        """Return the SMS / e-mail notification switches."""
        return self._devices(SmsEmail)

    def get_trends(self) -> list[Trend]:
        """Return the trends."""
        return self._devices(Trend)

    def get_vents(self) -> list[Vent]:
        """Return the ventilations."""
        return self._devices(Vent)


class MyGekkoHttpClient(MyGekkoClient):
    """Client talking to a MyGekko (local) or to the MyGekko Plus query API (cloud)."""

    def __init__(
        self,
        session: ClientSession,
        host: str,
        authentication_params: dict[str, str],
        scheme: str = "https",
        port: int | None = None,
    ) -> None:
        """Initialize the client."""
        super().__init__()
        self._session = session
        self._url = URL.build(scheme=scheme, host=host, port=port)
        self._authentication_params = authentication_params

    async def _get(self, path: str, extra_params: dict[str, str] | None = None) -> str:
        """Run a GET request, raises a MyGekkoError for HTTP errors."""
        params = self._authentication_params | (extra_params or {})
        async with self._session.get(
            self._url.with_path(path), params=params, timeout=REQUEST_TIMEOUT
        ) as response:
            body = await response.text()
            if response.status != 200:
                _LOGGER.error("MyGekko answered %s for %s", response.status, path)
                raise error_for_status(response.status, body)
            return body

    async def _get_json(self, path: str) -> dict:
        body = await self._get(path)
        try:
            return json.loads(body)
        except json.JSONDecodeError as err:
            raise MyGekkoError(f"Invalid JSON response from {path}") from err

    async def _fetch_resources(self) -> dict:
        return await self._get_json(API_PATH)

    async def _fetch_status(self) -> dict:
        return await self._get_json(API_PATH + "/status")

    async def write(self, resource_path: str, value: str) -> None:
        """Send a command to a resource."""
        path = f"{API_PATH}{resource_path}/scmd/set"
        _LOGGER.debug("Writing %s to %s", value, path)
        await self._get(path, {"value": value})


class MyGekkoQueryApiClient(MyGekkoHttpClient):
    """Client for the MyGekko Plus query API (cloud)."""

    def __init__(
        self, username: str, api_key: str, gekko_id: str, session: ClientSession
    ) -> None:
        """Initialize the client."""
        super().__init__(
            session,
            CLOUD_HOST,
            {"username": username, "key": api_key, "gekkoid": gekko_id},
        )


class MyGekkoLocalApiClient(MyGekkoHttpClient):
    """Client for the local API of a MyGekko."""

    def __init__(
        self,
        username: str,
        password: str,
        session: ClientSession,
        host: str,
        scheme: str = "https",
    ) -> None:
        """Initialize the client, `scheme` is "https" or "http"."""
        super().__init__(
            session, host, {"username": username, "password": password}, scheme=scheme
        )


class MyGekkoDemoModeClient(MyGekkoClient):
    """Client serving static demo data, no connection is made."""

    async def _load(self, name: str) -> dict:
        data = await asyncio.get_running_loop().run_in_executor(
            None, pkgutil.get_data, __package__, f"demo/{name}"
        )
        return json.loads(data)

    async def _fetch_resources(self) -> dict:
        return await self._load("api_var_demo_data.json")

    async def _fetch_status(self) -> dict:
        return await self._load("api_var_status_demo_data.json")

    async def write(self, resource_path: str, value: str) -> None:
        """Demo mode only logs commands."""
        _LOGGER.info("Demo mode: writing %s to %s", value, resource_path)


