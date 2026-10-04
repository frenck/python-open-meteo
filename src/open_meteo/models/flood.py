"""Models for the Open-Meteo flood API."""

# pylint: disable=too-many-instance-attributes
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from enum import StrEnum
from typing import Any

from mashumaro import field_options
from mashumaro.mixins.orjson import DataClassORJSONMixin

from ._split import _drop_suffixed, _split_members
from .common import TimeFormat


class FloodParameters(StrEnum):
    """Enum to represent the river discharge parameters available.

    All values are daily river discharge in cubic meters per second, for the
    river nearest to the location.
    """

    # River discharge of the forecast; with ensemble members, of the control
    # run
    RIVER_DISCHARGE = "river_discharge"

    # Statistics over all ensemble members: mean, median, maximum, minimum,
    # and the 25th and 75th percentile
    RIVER_DISCHARGE_MEAN = "river_discharge_mean"
    RIVER_DISCHARGE_MEDIAN = "river_discharge_median"
    RIVER_DISCHARGE_MAX = "river_discharge_max"
    RIVER_DISCHARGE_MIN = "river_discharge_min"
    RIVER_DISCHARGE_P25 = "river_discharge_p25"
    RIVER_DISCHARGE_P75 = "river_discharge_p75"


@dataclass
class DailyFlood(DataClassORJSONMixin):
    """Daily river discharge data."""

    time: list[date]
    river_discharge: list[float | None] | None = None
    river_discharge_mean: list[float | None] | None = None
    river_discharge_median: list[float | None] | None = None
    river_discharge_max: list[float | None] | None = None
    river_discharge_min: list[float | None] | None = None
    river_discharge_p25: list[float | None] | None = None
    river_discharge_p75: list[float | None] | None = None

    # Only set when ensemble members were requested, keyed by member number
    members: dict[int, DailyFlood] | None = None

    @classmethod
    def __pre_deserialize__(cls, d: dict[Any, Any]) -> dict[Any, Any]:
        """Group the ensemble members by member number."""
        return _split_members(d)


@dataclass
class DailyFloodUnits(DataClassORJSONMixin):
    """Daily river discharge data units."""

    time: TimeFormat | None = None
    river_discharge: str | None = None
    river_discharge_mean: str | None = None
    river_discharge_median: str | None = None
    river_discharge_max: str | None = None
    river_discharge_min: str | None = None
    river_discharge_p25: str | None = None
    river_discharge_p75: str | None = None

    @classmethod
    def __pre_deserialize__(cls, d: dict[Any, Any]) -> dict[Any, Any]:
        """Drop the units of ensemble members and previous runs."""
        return _drop_suffixed(d)


@dataclass
class Flood(DataClassORJSONMixin):
    """River discharge forecast."""

    elevation: float
    generation_time_ms: float = field(metadata=field_options(alias="generationtime_ms"))
    latitude: float
    longitude: float
    timezone: str
    timezone_abbreviation: str
    utc_offset_seconds: int
    daily_units: DailyFloodUnits | None = None
    daily: DailyFlood | None = None

    # Only set when multiple models were requested, keyed by the model name
    models: dict[str, Flood] | None = None
