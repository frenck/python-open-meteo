"""Asynchronous client for the Open-Meteo API."""
from .exceptions import OpenMeteoError
from .open_meteo import OpenMeteo

__all__ = [
    "OpenMeteo",
    "OpenMeteoError",
]
