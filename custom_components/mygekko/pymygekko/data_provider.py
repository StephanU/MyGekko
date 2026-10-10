"""Base implementation of the data provider"""
import asyncio
import json
import logging
import pkgutil
from abc import ABC
from abc import abstractmethod

from aiohttp import ClientSession
from aiohttp import ClientTimeout
from yarl import URL

from .resources import Entity

_LOGGER: logging.Logger = logging.getLogger(__name__)

# HTTP timeout for every request, so a hanging device can never block polling forever
REQUEST_TIMEOUT = ClientTimeout(total=15, sock_connect=8)


class DataSubscriberInterface:
    """Interface for data subscribers"""

    def update_status(self, status, hardware):
        """Method called on status updates"""

    def update_resources(self, resources):
        """Method called on resources updates"""


class EntityValueAccessor(DataSubscriberInterface):
    """Base class for entity values accessors"""

    def __init__(self):
        self._data = {}

    def get_value(self, entity: Entity, value_name: str) -> str | None:
        """Returns a data value of this entity"""
        if entity and entity.entity_id:
            if (
                entity.entity_id in self._data
                and value_name in self._data[entity.entity_id]
                and self._data[entity.entity_id][value_name]
            ):
                return self._data[entity.entity_id][value_name]
        return None


class DataProviderBase(ABC):
    """Base class for data providers"""

    def __init__(self):
        self._subscriber: list[DataSubscriberInterface] = []
        self._status = None
        self._resources = None

    @property
    def resources(self):
        """returns the read resources"""
        return self._resources

    @resources.setter
    def resources(self, resources):
        self._resources = resources
        for subscriber in self._subscriber:
            try:
                subscriber.update_resources(self._resources)
            except Exception:  # noqa: BLE001
                _LOGGER.exception(
                    "Updating resources of %s failed", type(subscriber).__name__
                )

    @property
    def status(self):
        """returns the read status"""
        return self._status

    @status.setter
    def status(self, status):
        self._status = status

        # current assumption is, that the hardware property is not set in legacy hardware (Slide)
        # but only in newer hardware (Slide 2, Nova)
        hardware = "legacy"
        network_data = ((status or {}).get("globals") or {}).get("network") or {}
        if (
            "hardware" in network_data
            and network_data["hardware"]
            and "value" in network_data["hardware"]
        ):
            hardware = network_data["hardware"]["value"]

        for subscriber in self._subscriber:
            try:
                subscriber.update_status(self._status, hardware)
            except Exception:  # noqa: BLE001
                _LOGGER.exception(
                    "Updating status of %s failed", type(subscriber).__name__
                )

    def subscribe(self, subscriber: DataSubscriberInterface):
        """Method to subscribe to data changes."""
        self._subscriber.append(subscriber)

    @abstractmethod
    async def read_data(self) -> None:
        """Reads data from the MyGekko API"""

    @abstractmethod
    async def write_data(self, resource_path: str, value: str):
        """Sends data to the MyGekko API"""

    @abstractmethod
    async def try_connect(self) -> None:
        """Tries to connect to the MyGekko API using the given credentials"""


class DummyDataProvider(DataProviderBase):
    """Dummy data provider returning static test data"""

    def __init__(self):
        super().__init__()

    async def try_connect(self) -> None:
        _LOGGER.debug("try_connect in DummyDataProvider")

    async def read_data(self) -> None:
        _LOGGER.debug("read_data in DummyDataProvider")
        loop = asyncio.get_running_loop()
        var_demo_data = await loop.run_in_executor(
            None, pkgutil.get_data, __name__, "api_var_demo_data.json"
        )
        self.resources = json.loads(var_demo_data)

        status_demo_data = await loop.run_in_executor(
            None, pkgutil.get_data, __name__, "api_var_status_demo_data.json"
        )
        self.status = json.loads(status_demo_data)

    async def write_data(self, resource_path: str, value: str):
        _LOGGER.info("Writing to %s %s", resource_path, value)


class DataProvider(DataProviderBase):
    """Data provider accessing the MyGekko API"""

    def __init__(
        self, url: URL, authentication_params: dict[str, str], session: ClientSession
    ):
        super().__init__()
        self._url = url
        self._authentication_params = authentication_params
        self._session = session

    async def _get(self, path: str, extra_params: dict[str, str] | None = None) -> str:
        """Executes a GET request and returns the response body.

        Raises a MyGekkoError subclass on any HTTP error status.
        """
        params = self._authentication_params | (extra_params or {})
        async with self._session.get(
            self._url.with_path(path), params=params, timeout=REQUEST_TIMEOUT
        ) as resp:
            response_text = await resp.text()
            if resp.status != 200:
                self.handle_api_error(resp.status, response_text)
            return response_text

    async def _get_json(self, path: str) -> dict:
        """Executes a GET request and parses the JSON response."""
        response_text = await self._get(path)
        try:
            return json.loads(response_text)
        except json.JSONDecodeError as err:
            _LOGGER.error("Json parsing of the response of %s failed", path)
            raise MyGekkoError(f"Invalid JSON response from {path}") from err

    async def try_connect(self) -> None:
        _LOGGER.debug("try_connect in DataProvider")
        await self._get("/api/v1/var")

    async def read_data(self) -> None:
        _LOGGER.debug("read_data in DataProvider")
        # Fetch both documents first and only publish them when both succeeded,
        # so subscribers never see resources and status from different polls.
        resources = await self._get_json("/api/v1/var")
        status = await self._get_json("/api/v1/var/status")
        self.resources = resources
        self.status = status
        _LOGGER.debug("read_data end")

    async def write_data(self, resource_path: str, value: str):
        resource_url = "/api/v1/var" + resource_path + "/scmd/set"

        _LOGGER.debug("Writing data %s to %s", value, resource_url)
        await self._get(resource_url, {"value": value})

    def handle_api_error(self, response_status, response_text):
        """Handles the api response in case of errors"""
        if response_status == 400:
            _LOGGER.error("MyGekkoBadRequest %s", response_text)
            raise MyGekkoBadRequest()
        elif response_status == 403:
            _LOGGER.error("MyGekkoForbidden %s", response_text)
            raise MyGekkoForbidden()
        elif response_status == 404:
            _LOGGER.error("MyGekkoNotFound %s", response_text)
            raise MyGekkoNotFound()
        elif response_status == 405:
            _LOGGER.error("MyGekkoMethodNotAllowed %s", response_text)
            raise MyGekkoMethodNotAllowed()
        elif response_status == 410:
            _LOGGER.error("MyGekkoGone %s", response_text)
            raise MyGekkoGone()
        elif response_status == 429:
            _LOGGER.error("MyGekkoTooManyRequests %s", response_text)
            raise MyGekkoTooManyRequests()
        elif response_status == 444:
            _LOGGER.error("MyGekkoNoResponse %s", response_text)
            raise MyGekkoNoResponse()
        else:
            raise MyGekkoError(f"HTTP {response_status}")


class MyGekkoError(Exception):
    """Base MyGekko exception."""


class MyGekkoBadRequest(MyGekkoError):
    """MyGekko Bad Request exception."""


class MyGekkoForbidden(MyGekkoError):
    """MyGekko Forbidden exception."""


class MyGekkoNotFound(MyGekkoError):
    """MyGekko Not Found exception."""


class MyGekkoMethodNotAllowed(MyGekkoError):
    """MyGekko Method Not Allowed exception."""


class MyGekkoGone(MyGekkoError):
    """MyGekko Gone exception."""


class MyGekkoTooManyRequests(MyGekkoError):
    """MyGekko Too Many Requests exception."""


class MyGekkoNoResponse(MyGekkoError):
    """MyGekko No Response exception."""
