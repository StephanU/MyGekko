"""Exceptions raised by the MyGekko API client."""


class MyGekkoError(Exception):
    """Base MyGekko exception."""


class MyGekkoBadRequest(MyGekkoError):
    """The request was rejected (HTTP 400)."""


class MyGekkoForbidden(MyGekkoError):
    """The credentials or permissions are not sufficient (HTTP 401/403)."""


class MyGekkoNotFound(MyGekkoError):
    """The requested resource does not exist (HTTP 404)."""


class MyGekkoMethodNotAllowed(MyGekkoError):
    """The method is not allowed for the resource (HTTP 405)."""


class MyGekkoGone(MyGekkoError):
    """The resource is gone (HTTP 410)."""


class MyGekkoTooManyRequests(MyGekkoError):
    """The rate limit of the MyGekko API was exceeded (HTTP 429)."""


class MyGekkoNoResponse(MyGekkoError):
    """The MyGekko did not respond (HTTP 444)."""


_STATUS_ERRORS: dict[int, type[MyGekkoError]] = {
    400: MyGekkoBadRequest,
    401: MyGekkoForbidden,
    403: MyGekkoForbidden,
    404: MyGekkoNotFound,
    405: MyGekkoMethodNotAllowed,
    410: MyGekkoGone,
    429: MyGekkoTooManyRequests,
    444: MyGekkoNoResponse,
}


def error_for_status(status: int, body: str = "") -> MyGekkoError:
    """Return the matching exception for an HTTP error status."""
    error_class = _STATUS_ERRORS.get(status, MyGekkoError)
    return error_class(f"HTTP {status} {body[:200]}".strip())
