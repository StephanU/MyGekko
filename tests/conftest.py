"""Global fixtures for MyGekko integration."""
from unittest.mock import patch

import pytest
from PyMyGekko.data_provider import MyGekkoError

pytest_plugins = "pytest_homeassistant_custom_component"

# The integration talks to one of these two clients depending on the configured
# connection type. Demo mode needs no patching at all, it ships its own data.
API_CLIENTS = (
    "PyMyGekko.MyGekkoQueryApiClient",
    "PyMyGekko.MyGekkoLocalApiClient",
)


# This fixture is used to prevent HomeAssistant from attempting to create and dismiss persistent
# notifications. These calls would fail without this fixture since the persistent_notification
# integration is never loaded during a test.
@pytest.fixture(name="skip_notifications", autouse=True)
def skip_notifications_fixture():
    """Skip notification calls."""
    with patch("homeassistant.components.persistent_notification.async_create"), patch(
        "homeassistant.components.persistent_notification.async_dismiss"
    ):
        yield


@pytest.fixture(name="auto_enable_custom_integrations", autouse=True)
def auto_enable_custom_integrations_fixture(enable_custom_integrations):
    """Load the custom integration in every test."""
    yield


@pytest.fixture(name="bypass_get_data")
def bypass_get_data_fixture():
    """Skip calls to get data from the API."""
    with patch(f"{API_CLIENTS[0]}.read_data"), patch(f"{API_CLIENTS[1]}.read_data"):
        yield


@pytest.fixture(name="bypass_try_connect")
def bypass_try_connect_fixture():
    """Skip calls to connect to the API."""
    with patch(f"{API_CLIENTS[0]}.try_connect"), patch(f"{API_CLIENTS[1]}.try_connect"):
        yield


@pytest.fixture(name="error_on_try_connect")
def error_on_try_connect_fixture():
    """Simulate an error while connecting to the API."""
    with patch(
        f"{API_CLIENTS[0]}.try_connect", side_effect=MyGekkoError
    ), patch(f"{API_CLIENTS[1]}.try_connect", side_effect=MyGekkoError):
        yield


@pytest.fixture(name="error_on_get_data")
def error_on_get_data_fixture():
    """Simulate an error while retrieving data from the API."""
    with patch(f"{API_CLIENTS[0]}.read_data", side_effect=MyGekkoError), patch(
        f"{API_CLIENTS[1]}.read_data", side_effect=MyGekkoError
    ):
        yield
