"""Asynchronous client for the Open-Meteo API."""

from __future__ import annotations


class OpenMeteoError(Exception):
    """Generic OpenMeteo exception."""


class OpenMeteoConnectionError(OpenMeteoError):
    """OpenMeteo connection exception."""


class OpenMeteoResponseError(OpenMeteoError):
    """The Open-Meteo API responded with an error.

    The status is the HTTP status code, and the reason the explanation the
    API gave, like "Latitude must be in range of -90 to 90°.".
    """

    def __init__(self, status: int, reason: str) -> None:
        """Initialize the error, with the reason as message."""
        super().__init__(reason)
        self.status = status
        self.reason = reason


class OpenMeteoRateLimitError(OpenMeteoResponseError):
    """The Open-Meteo API rejected the request, as too many were made.

    The retry after is how many seconds to wait before trying again, if the
    API said so.
    """

    def __init__(self, status: int, reason: str, retry_after: int | None) -> None:
        """Initialize the error, with how long to wait before retrying."""
        super().__init__(status, reason)
        self.retry_after = retry_after
