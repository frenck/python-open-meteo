"""Models for the Open-Meteo geocoding API."""

# pylint: disable=too-many-instance-attributes
from __future__ import annotations

from dataclasses import dataclass, field

from mashumaro import field_options
from mashumaro.mixins.orjson import DataClassORJSONMixin


@dataclass
class GeocodingResult(DataClassORJSONMixin):
    """Geocoding result item."""

    geo_id: int = field(metadata=field_options(alias="id"))
    feature_code: str
    latitude: float
    longitude: float
    name: str
    timezone: str

    # Not every location has these, Antarctica or some islands for example
    country_code: str | None = None
    country_id: int | None = None
    country: str | None = None
    elevation: float | None = None

    admin1_id: int | None = None
    admin1: str | None = None
    admin2_id: int | None = None
    admin2: str | None = None
    admin3_id: int | None = None
    admin3: str | None = None
    admin4_id: int | None = None
    admin4: str | None = None
    population: int | None = None
    postcodes: list[str] | None = None
    ranking: float | None = None


@dataclass
class Geocoding(DataClassORJSONMixin):
    """Geocoding search result."""

    generation_time_ms: float = field(metadata=field_options(alias="generationtime_ms"))
    results: list[GeocodingResult] | None = None
