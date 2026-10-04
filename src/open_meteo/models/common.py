"""Enums shared by the Open-Meteo APIs."""

from __future__ import annotations

from enum import StrEnum, auto


class TemperatureUnit(StrEnum):
    """Enum to represent the temperature units available."""

    CELSIUS = auto()
    FAHRENHEIT = auto()


class WindSpeedUnit(StrEnum):
    """Enum to represent the wind speed units available."""

    KILOMETERS_PER_HOUR = "kmh"
    KNOTS = "kn"
    METERS_PER_SECOND = "ms"
    MILES_PER_HOUR = "mph"


class PrecipitationUnit(StrEnum):
    """Enum to represent the precipitation units available."""

    MILLIMETERS = "mm"
    INCHES = "inch"


class TimeFormat(StrEnum):
    """Enum to represent the time formats available."""

    ISO_8601 = "iso8601"
    UNIXTIME = "unixtime"


class CellSelection(StrEnum):
    """Enum to represent how a location is matched to a weather model grid cell."""

    # Prefer grid cells on land with a similar elevation (the API default)
    LAND = "land"

    # Prefer grid cells on sea
    SEA = "sea"

    # Use the nearest grid cell, regardless of land or sea
    NEAREST = "nearest"


class TemporalResolution(StrEnum):
    """Enum to represent the time resolutions data can be aggregated into."""

    # The native time resolution of the weather model
    NATIVE = "native"

    # Every 15 or 30 minutes, in the hourly data; unlike the 15-minutely
    # data, which is a section of its own
    MINUTELY_15 = "minutely_15"
    MINUTELY_30 = "minutely_30"

    HOURLY = "hourly"
    HOURLY_3 = "hourly_3"
    HOURLY_6 = "hourly_6"
