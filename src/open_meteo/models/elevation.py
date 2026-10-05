"""Models for the Open-Meteo elevation API."""

from dataclasses import dataclass

from mashumaro.mixins.orjson import DataClassORJSONMixin


@dataclass
class Elevation(DataClassORJSONMixin):
    """Elevation lookup result."""

    elevation: list[float]
