"""Asynchronous client for the Open-Meteo API."""


class OpenMeteoError(Exception):
    """Generic OpenMeteo exception."""


class OpenMeteoConnectionError(OpenMeteoError):
    """OpenMeteo connection exception."""
