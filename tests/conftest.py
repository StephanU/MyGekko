"""Global fixtures for MyGekko integration."""
from unittest.mock import patch

import pytest

pytest_plugins = "pytest_homeassistant_custom_component"


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


# This fixture, when used, will result in calls to get_data to return None. To have the call
# return a value, we would add the `return_value=<VALUE_TO_RETURN>` parameter to the patch call.
@pytest.fixture(name="bypass_get_data")
def bypass_get_data_fixture():
    """Skip calls to get data from API."""
    with patch("custom_components.mygekko.MyGekkoApiClient.get_data"):
        yield


# This fixture, when used, will result in calls to try_connect to return None. To have the call
# return a value, we would add the `return_value=<VALUE_TO_RETURN>` parameter to the patch call.
@pytest.fixture(name="bypass_try_connect")
def bypass_try_connect_fixture():
    """Skip calls to get data from API."""
    with patch("custom_components.mygekko.MyGekkoApiClient.try_connect"):
        yield


# In this fixture, we are forcing calls to try_connect to raise an Exception. This is useful
# for exception handling.
@pytest.fixture(name="error_on_try_connect")
def error_try_connect_fixture():
    """Simulate error when retrieving data from API."""
    with patch(
        "custom_components.mygekko.MyGekkoApiClient.try_connect",
        side_effect=Exception,
    ):
        yield
