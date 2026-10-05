"""Models for the Open-Meteo APIs."""

from mashumaro.mixins.orjson import DataClassORJSONMixin

from .air_quality import (
    AirQuality,
    AirQualityDomain,
    AirQualityParameters,
    CurrentAirQuality,
    CurrentAirQualityUnits,
    HourlyAirQuality,
    HourlyAirQualityUnits,
)
from .common import (
    CellSelection,
    PrecipitationUnit,
    TemperatureUnit,
    TemporalResolution,
    TimeFormat,
    WindSpeedUnit,
)
from .elevation import Elevation
from .flood import (
    DailyFlood,
    DailyFloodUnits,
    Flood,
    FloodParameters,
)
from .forecast import (
    CurrentForecast,
    CurrentForecastUnits,
    DailyForecast,
    DailyForecastUnits,
    DailyParameters,
    Forecast,
    ForecastSection,
    HeightLevelCurrent,
    HeightLevelForecast,
    HeightLevelForecastUnits,
    HeightLevelVariable,
    HourlyForecast,
    HourlyForecastUnits,
    HourlyParameters,
    Minutely15Forecast,
    Minutely15ForecastUnits,
    PressureLevelCurrent,
    PressureLevelForecast,
    PressureLevelForecastUnits,
    PressureLevelVariable,
)
from .geocoding import (
    Geocoding,
    GeocodingResult,
)
from .marine import (
    CurrentMarine,
    CurrentMarineUnits,
    DailyMarine,
    DailyMarineUnits,
    HourlyMarine,
    HourlyMarineUnits,
    LengthUnit,
    Marine,
    MarineDailyParameters,
    MarineParameters,
    Minutely15Marine,
    Minutely15MarineUnits,
)
from .seasonal import (
    MonthlySeasonal,
    MonthlySeasonalUnits,
    Seasonal,
    SeasonalMonthlyParameters,
    SeasonalWeeklyParameters,
    WeeklySeasonal,
    WeeklySeasonalUnits,
)

__all__ = [
    "AirQuality",
    "AirQualityDomain",
    "AirQualityParameters",
    "CellSelection",
    "CurrentAirQuality",
    "CurrentAirQualityUnits",
    "CurrentForecast",
    "CurrentForecastUnits",
    "CurrentMarine",
    "CurrentMarineUnits",
    "DailyFlood",
    "DailyFloodUnits",
    "DailyForecast",
    "DailyForecastUnits",
    "DailyMarine",
    "DailyMarineUnits",
    "DailyParameters",
    "Elevation",
    "Flood",
    "FloodParameters",
    "Forecast",
    "ForecastSection",
    "Geocoding",
    "GeocodingResult",
    "HeightLevelCurrent",
    "HeightLevelForecast",
    "HeightLevelForecastUnits",
    "HeightLevelVariable",
    "HourlyAirQuality",
    "HourlyAirQualityUnits",
    "HourlyForecast",
    "HourlyForecastUnits",
    "HourlyMarine",
    "HourlyMarineUnits",
    "HourlyParameters",
    "LengthUnit",
    "Marine",
    "MarineDailyParameters",
    "MarineParameters",
    "Minutely15Forecast",
    "Minutely15ForecastUnits",
    "Minutely15Marine",
    "Minutely15MarineUnits",
    "MonthlySeasonal",
    "MonthlySeasonalUnits",
    "PrecipitationUnit",
    "PressureLevelCurrent",
    "PressureLevelForecast",
    "PressureLevelForecastUnits",
    "PressureLevelVariable",
    "Seasonal",
    "SeasonalMonthlyParameters",
    "SeasonalWeeklyParameters",
    "TemperatureUnit",
    "TemporalResolution",
    "TimeFormat",
    "WeeklySeasonal",
    "WeeklySeasonalUnits",
    "WindSpeedUnit",
]


def _compile_models() -> None:
    """Compile the parsing of the models mashumaro couldn't compile yet.

    A model that refers to itself, or to one defined after it, like the
    members of an hourly forecast, has those annotations quoted. mashumaro
    can't resolve them while the model is being defined, so it compiles that
    model on first use instead. Under freezegun, as in many test suites, date
    and datetime are fakes by then, also within mashumaro, and parsing fails.
    Now that every model exists, compile those right away.
    """
    for name in __all__:
        model = globals()[name]
        if not (isinstance(model, type) and issubclass(model, DataClassORJSONMixin)):
            continue

        if any(
            isinstance(annotation, str) for annotation in model.__annotations__.values()
        ):
            model.__init_subclass__()


_compile_models()
