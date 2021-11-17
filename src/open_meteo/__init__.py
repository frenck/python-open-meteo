"""Asynchronous client for the Open-Meteo API."""
from .exceptions import OpenMeteoConnectionError, OpenMeteoError
from .models import (
    CurrentWeather,
    DailyForecast,
    DailyForecastUnits,
    DailyParameters,
    Forecast,
    Geocoding,
    GeocodingResult,
    HourlyForecast,
    HourlyForecastUnits,
    HourlyParameters,
    PrecipitationUnit,
    TemperatureUnit,
    TimeFormat,
    WindSpeedUnit,
)
from .open_meteo import OpenMeteo

__all__ = [
    "CurrentWeather",
    "DailyForecast",
    "DailyForecastUnits",
    "DailyParameters",
    "Forecast",
    "Geocoding",
    "GeocodingResult",
    "HourlyForecast",
    "HourlyForecastUnits",
    "HourlyParameters",
    "OpenMeteo",
    "OpenMeteoConnectionError",
    "OpenMeteoError",
    "PrecipitationUnit",
    "TemperatureUnit",
    "TimeFormat",
    "WindSpeedUnit",
]
