"""Tests for the Open-Meteo client."""

# pylint: disable=protected-access

import asyncio
import re
from datetime import date, datetime
from typing import Self, cast
from urllib.parse import unquote
from zoneinfo import ZoneInfo

import aiohttp
import pytest
from aioresponses import aioresponses
from syrupy.assertion import SnapshotAssertion
from yarl import URL

from open_meteo import (
    AirQualityDomain,
    AirQualityParameters,
    CellSelection,
    DailyParameters,
    FloodParameters,
    ForecastSection,
    HourlyParameters,
    LengthUnit,
    MarineDailyParameters,
    MarineParameters,
    OpenMeteo,
    PrecipitationUnit,
    PressureLevelVariable,
    SeasonalMonthlyParameters,
    SeasonalWeeklyParameters,
    TemperatureUnit,
    TemporalResolution,
    WindSpeedUnit,
)
from open_meteo.exceptions import (
    OpenMeteoConnectionError,
    OpenMeteoError,
    OpenMeteoRateLimitError,
    OpenMeteoResponseError,
)

from .conftest import load_fixture

FORECAST_URL = "https://api.open-meteo.com/v1/forecast"
HISTORICAL_FORECAST_URL = "https://historical-forecast-api.open-meteo.com/v1/forecast"
HISTORICAL_WEATHER_URL = "https://archive-api.open-meteo.com/v1/archive"
AIR_QUALITY_URL = "https://air-quality-api.open-meteo.com/v1/air-quality"
GEOCODING_URL = "https://geocoding-api.open-meteo.com/v1/search"
GEOCODING_BY_ID_URL = "https://geocoding-api.open-meteo.com/v1/get"
ELEVATION_URL = "https://api.open-meteo.com/v1/elevation"
MARINE_URL = "https://marine-api.open-meteo.com/v1/marine"
FLOOD_URL = "https://flood-api.open-meteo.com/v1/flood"
CLIMATE_URL = "https://climate-api.open-meteo.com/v1/climate"
ENSEMBLE_URL = "https://ensemble-api.open-meteo.com/v1/ensemble"
SEASONAL_URL = "https://seasonal-api.open-meteo.com/v1/seasonal"
PREVIOUS_RUNS_URL = "https://previous-runs-api.open-meteo.com/v1/forecast"
SINGLE_RUN_URL = "https://single-runs-api.open-meteo.com/v1/forecast"
SATELLITE_URL = "https://satellite-api.open-meteo.com/v1/archive"


def mock_endpoint(
    responses: aioresponses,
    url: str,
    fixture: str,
) -> None:
    """Mock an endpoint, regardless of the query string sent."""
    responses.get(
        re.compile(rf"^{re.escape(url)}\?.*$"),
        status=200,
        body=load_fixture(fixture),
        content_type="application/json",
    )


def requested_query(responses: aioresponses) -> dict[str, str]:
    """Return the query of the one request that was made."""
    requests = responses.requests
    assert requests is not None
    assert len(requests) == 1
    (_method, url), _calls = next(iter(requests.items()))

    # aioresponses re-encodes the URL it records, so commas and slashes come
    # back as %2C and %2F. Undo that to compare against what was really sent.
    return {key: unquote(value) for key, value in url.query.items()}


async def test_json_request(
    responses: aioresponses,
    open_meteo_client: OpenMeteo,
) -> None:
    """Test JSON response is handled correctly."""
    responses.get(
        "http://example.com/api/",
        status=200,
        body='{"status": "ok"}',
        content_type="application/json",
    )
    response = await open_meteo_client._request(URL("http://example.com/api/"))
    assert response == '{"status": "ok"}'


async def test_internal_session(responses: aioresponses) -> None:
    """Test the client creates a session and closes it again."""
    responses.get(
        "http://example.com/api/",
        status=200,
        body='{"status": "ok"}',
        content_type="application/json",
    )
    async with OpenMeteo() as open_meteo:
        response = await open_meteo._request(URL("http://example.com/api/"))
        assert response == '{"status": "ok"}'
        assert open_meteo.session is not None

    assert open_meteo.session.closed


async def test_external_session_is_left_open(responses: aioresponses) -> None:
    """Test a session passed in by the caller is not closed by the client."""
    responses.get(
        "http://example.com/api/",
        status=200,
        body='{"status": "ok"}',
        content_type="application/json",
    )
    async with aiohttp.ClientSession() as session:
        async with OpenMeteo(session=session) as open_meteo:
            await open_meteo._request(URL("http://example.com/api/"))

        assert not session.closed


async def test_forecast(
    responses: aioresponses,
    open_meteo_client: OpenMeteo,
    snapshot: SnapshotAssertion,
) -> None:
    """Test requesting a forecast with every variable available."""
    mock_endpoint(responses, FORECAST_URL, "forecast.json")

    forecast = await open_meteo_client.forecast(
        latitude=52.27,
        longitude=6.87417,
        timezone="Europe/Amsterdam",
        current=list(HourlyParameters),
        daily=list(DailyParameters),
        hourly=list(HourlyParameters),
    )

    query = requested_query(responses)
    assert query["current"] == ",".join(HourlyParameters)
    assert query["daily"] == ",".join(DailyParameters)
    assert query["hourly"] == ",".join(HourlyParameters)
    assert query["timezone"] == "Europe/Amsterdam"
    assert forecast == snapshot


async def test_forecast_options(
    responses: aioresponses,
    open_meteo_client: OpenMeteo,
) -> None:
    """Test the forecast options end up in the query as the API expects."""
    mock_endpoint(responses, FORECAST_URL, "forecast_minimal.json")

    await open_meteo_client.forecast(
        latitude=52.27,
        longitude=6.87417,
        forecast_days=1,
        past_days=1,
        precipitation_unit=PrecipitationUnit.INCHES,
        temperature_unit=TemperatureUnit.FAHRENHEIT,
        wind_speed_unit=WindSpeedUnit.KNOTS,
    )

    query = requested_query(responses)
    assert query["forecast_days"] == "1"
    assert query["past_days"] == "1"
    assert query["precipitation_unit"] == "inch"
    assert query["temperature_unit"] == "fahrenheit"
    assert query["wind_speed_unit"] == "kn"


async def test_forecast_defaults(
    responses: aioresponses,
    open_meteo_client: OpenMeteo,
    snapshot: SnapshotAssertion,
) -> None:
    """Test requesting a forecast with only a location."""
    mock_endpoint(responses, FORECAST_URL, "forecast_minimal.json")

    forecast = await open_meteo_client.forecast(latitude=52.27, longitude=6.87417)

    # Anything left unset is left out of the query, so the API defaults apply
    assert requested_query(responses) == {
        "latitude": "52.27",
        "longitude": "6.87417",
        "past_days": "0",
        "precipitation_unit": "mm",
        "temperature_unit": "celsius",
        "timeformat": "iso8601",
        "timezone": "UTC",
        "wind_speed_unit": "kmh",
    }
    assert forecast.current is None
    assert forecast.daily is None
    assert forecast.hourly is None
    assert forecast == snapshot


async def test_forecast_minutely_15(
    responses: aioresponses,
    open_meteo_client: OpenMeteo,
    snapshot: SnapshotAssertion,
) -> None:
    """Test requesting 15-minutely data."""
    mock_endpoint(responses, FORECAST_URL, "forecast_minutely_15.json")

    forecast = await open_meteo_client.forecast(
        latitude=52.27,
        longitude=6.87417,
        minutely_15=[
            HourlyParameters.TEMPERATURE_2M,
            HourlyParameters.PRECIPITATION,
            HourlyParameters.IS_DAY,
        ],
        forecast_minutely_15=4,
        past_minutely_15=0,
    )

    query = requested_query(responses)
    assert query["minutely_15"] == "temperature_2m,precipitation,is_day"
    assert query["forecast_minutely_15"] == "4"
    assert query["past_minutely_15"] == "0"

    assert forecast.minutely_15 is not None
    assert len(forecast.minutely_15.time) == 4
    assert forecast.minutely_15.temperature_2m is not None
    assert forecast.minutely_15_units is not None
    assert forecast.minutely_15_units.temperature_2m == "°C"
    assert forecast == snapshot


async def test_forecast_time_range(
    responses: aioresponses,
    open_meteo_client: OpenMeteo,
) -> None:
    """Test dates and hours are sent in the ISO 8601 format the API expects."""
    mock_endpoint(responses, FORECAST_URL, "forecast_minimal.json")

    await open_meteo_client.forecast(
        latitude=52.27,
        longitude=6.87417,
        start_date=date(2026, 10, 4),
        end_date=date(2026, 10, 5),
        # Naive on purpose: the API reads these as local time in the timezone
        start_hour=datetime(2026, 10, 4, 6, 0, 30),  # noqa: DTZ001
        end_hour=datetime(2026, 10, 4, 18, 0),  # noqa: DTZ001
        forecast_hours=6,
        past_hours=2,
        temporal_resolution=TemporalResolution.HOURLY_3,
    )

    query = requested_query(responses)
    assert query["start_date"] == "2026-10-04"
    assert query["end_date"] == "2026-10-05"
    # The API takes hours without seconds
    assert query["start_hour"] == "2026-10-04T06:00"
    assert query["end_hour"] == "2026-10-04T18:00"
    assert query["forecast_hours"] == "6"
    assert query["past_hours"] == "2"
    assert query["temporal_resolution"] == "hourly_3"


async def test_forecast_location_options(
    responses: aioresponses,
    open_meteo_client: OpenMeteo,
) -> None:
    """Test the options that tune how the location is modeled."""
    mock_endpoint(responses, FORECAST_URL, "forecast_minimal.json")

    await open_meteo_client.forecast(
        latitude=52.27,
        longitude=6.87417,
        elevation=float("nan"),
        cell_selection=CellSelection.SEA,
        tilt=35,
        azimuth=-10.5,
    )

    query = requested_query(responses)
    # NaN switches off elevation downscaling, and yarl can't encode it itself
    assert query["elevation"] == "nan"
    assert query["cell_selection"] == "sea"
    assert query["tilt"] == "35"
    assert query["azimuth"] == "-10.5"


async def test_forecast_single_model(
    responses: aioresponses,
    open_meteo_client: OpenMeteo,
) -> None:
    """Test a single model keeps the data on the forecast itself."""
    mock_endpoint(responses, FORECAST_URL, "forecast_16_days.json")

    forecast = await open_meteo_client.forecast(
        latitude=52.27,
        longitude=6.87417,
        hourly=[HourlyParameters.TEMPERATURE_2M],
        models=["icon_seamless"],
    )

    assert requested_query(responses)["models"] == "icon_seamless"
    assert forecast.hourly is not None
    assert forecast.models is None


async def test_forecast_multiple_models(
    responses: aioresponses,
    open_meteo_client: OpenMeteo,
    snapshot: SnapshotAssertion,
) -> None:
    """Test the data of each model ends up in a forecast of its own.

    The fixture is a real response for Zurich, where both icon_seamless and
    meteoswiss_icon_seamless have data. The latter also ends in
    _icon_seamless, so the longest model name has to win.
    """
    mock_endpoint(responses, FORECAST_URL, "forecast_models.json")

    models = ["icon_seamless", "meteoswiss_icon_seamless", "gfs_seamless"]
    forecast = await open_meteo_client.forecast(
        latitude=47.37,
        longitude=8.54,
        current=[HourlyParameters.TEMPERATURE_2M],
        minutely_15=[HourlyParameters.TEMPERATURE_2M],
        hourly=[HourlyParameters.TEMPERATURE_2M, HourlyParameters.WEATHER_CODE],
        daily=[DailyParameters.TEMPERATURE_2M_MAX],
        models=models,
    )

    assert requested_query(responses)["models"] == ",".join(models)

    # The current conditions always come from a single model
    assert forecast.current is not None
    assert forecast.hourly is None
    assert forecast.daily is None
    assert forecast.minutely_15 is None

    assert forecast.models is not None
    assert list(forecast.models) == models
    icon = forecast.models["icon_seamless"]
    meteoswiss = forecast.models["meteoswiss_icon_seamless"]
    assert icon.current is None
    assert icon.hourly is not None
    assert meteoswiss.hourly is not None
    assert icon.hourly.temperature_2m != meteoswiss.hourly.temperature_2m
    assert icon.hourly.time == meteoswiss.hourly.time
    assert icon.hourly_units is not None
    assert icon.hourly_units.temperature_2m == "°C"
    assert icon.daily is not None
    assert icon.minutely_15 is not None
    assert forecast == snapshot


async def test_forecast_models_with_one_covering(
    responses: aioresponses,
    open_meteo_client: OpenMeteo,
) -> None:
    """Test data is not split when only one of the models covers the location.

    meteoswiss_icon_seamless doesn't cover Enschede. The API then leaves out
    that model, and returns the other one without a model suffix, so there is
    no telling which model the data is from. It stays on the forecast itself.
    """
    mock_endpoint(responses, FORECAST_URL, "forecast_models_one_covering.json")

    forecast = await open_meteo_client.forecast(
        latitude=52.27,
        longitude=6.87417,
        hourly=[HourlyParameters.TEMPERATURE_2M],
        models=["icon_seamless", "meteoswiss_icon_seamless"],
    )

    assert forecast.models is None
    assert forecast.hourly is not None
    assert forecast.hourly.temperature_2m is not None


async def test_forecast_pressure_levels(
    responses: aioresponses,
    open_meteo_client: OpenMeteo,
    snapshot: SnapshotAssertion,
) -> None:
    """Test pressure level data is grouped by pressure level."""
    mock_endpoint(responses, FORECAST_URL, "forecast_pressure_levels.json")

    forecast = await open_meteo_client.forecast(
        latitude=52.27,
        longitude=6.87417,
        hourly=[HourlyParameters.TEMPERATURE_2M],
        pressure_level_variables=[
            PressureLevelVariable.TEMPERATURE,
            PressureLevelVariable.WIND_SPEED,
        ],
        pressure_levels=[850, 500],
    )

    # Every variable is combined with every level, next to the regular ones
    assert requested_query(responses)["hourly"] == (
        "temperature_2m,temperature_850hPa,temperature_500hPa,"
        "wind_speed_850hPa,wind_speed_500hPa"
    )

    assert forecast.hourly is not None
    assert forecast.hourly.temperature_2m is not None
    assert forecast.hourly.pressure_levels is not None
    assert list(forecast.hourly.pressure_levels) == [850, 500]
    level = forecast.hourly.pressure_levels[850]
    assert level.temperature is not None
    assert level.wind_speed is not None
    assert level.dew_point is None

    assert forecast.hourly_units is not None
    assert forecast.hourly_units.pressure_levels is not None
    assert forecast.hourly_units.pressure_levels[850].temperature == "°C"
    assert forecast == snapshot


async def test_forecast_pressure_levels_with_models(
    responses: aioresponses,
    open_meteo_client: OpenMeteo,
) -> None:
    """Test pressure level data is grouped per model as well."""
    mock_endpoint(responses, FORECAST_URL, "forecast_pressure_levels_models.json")

    forecast = await open_meteo_client.forecast(
        latitude=52.27,
        longitude=6.87417,
        hourly=[HourlyParameters.TEMPERATURE_2M],
        pressure_level_variables=[
            PressureLevelVariable.TEMPERATURE,
            PressureLevelVariable.WIND_SPEED,
        ],
        pressure_levels=[850, 500],
        models=["icon_seamless", "gfs_seamless"],
    )

    assert forecast.models is not None
    icon = forecast.models["icon_seamless"].hourly
    gfs = forecast.models["gfs_seamless"].hourly
    assert icon is not None
    assert gfs is not None
    assert icon.pressure_levels is not None
    assert gfs.pressure_levels is not None
    assert icon.pressure_levels[500].temperature is not None
    assert icon.pressure_levels[500].temperature != gfs.pressure_levels[500].temperature


@pytest.mark.parametrize(
    ("variables", "levels"),
    [
        ([PressureLevelVariable.TEMPERATURE], None),
        (None, [850]),
    ],
)
async def test_forecast_pressure_levels_incomplete(
    open_meteo_client: OpenMeteo,
    variables: list[PressureLevelVariable] | None,
    levels: list[int] | None,
) -> None:
    """Test giving only one of the two pressure level parameters raises."""
    with pytest.raises(ValueError, match="Both pressure_level_variables"):
        await open_meteo_client.forecast(
            latitude=52.27,
            longitude=6.87417,
            pressure_level_variables=variables,
            pressure_levels=levels,
        )


async def test_forecast_pressure_level_sections(
    responses: aioresponses,
    open_meteo_client: OpenMeteo,
    snapshot: SnapshotAssertion,
) -> None:
    """Test pressure levels for the current conditions and 15-minutely data."""
    mock_endpoint(responses, FORECAST_URL, "forecast_pressure_level_sections.json")

    forecast = await open_meteo_client.forecast(
        latitude=52.27,
        longitude=6.87417,
        current=[HourlyParameters.TEMPERATURE_2M],
        minutely_15=[HourlyParameters.TEMPERATURE_2M],
        pressure_level_variables=[
            PressureLevelVariable.TEMPERATURE,
            PressureLevelVariable.WIND_SPEED,
        ],
        pressure_levels=[850],
        pressure_level_sections=[ForecastSection.CURRENT, ForecastSection.MINUTELY_15],
        forecast_minutely_15=2,
    )

    # Only the chosen sections get the pressure levels
    query = requested_query(responses)
    assert query["current"] == "temperature_2m,temperature_850hPa,wind_speed_850hPa"
    assert query["minutely_15"] == (
        "temperature_2m,temperature_850hPa,wind_speed_850hPa"
    )
    assert "hourly" not in query

    assert forecast.current is not None
    assert forecast.current.pressure_levels is not None
    assert forecast.current.pressure_levels[850].temperature is not None
    assert forecast.current.pressure_levels[850].wind_speed is not None
    assert forecast.current_units is not None
    assert forecast.current_units.pressure_levels is not None
    assert forecast.current_units.pressure_levels[850].wind_speed == "km/h"
    assert forecast.minutely_15 is not None
    assert forecast.minutely_15.pressure_levels is not None
    assert forecast == snapshot


async def test_pressure_level_sections_without_current(
    open_meteo_client: OpenMeteo,
) -> None:
    """Test current conditions can't be chosen where an API doesn't have those."""
    with pytest.raises(ValueError, match="There is no current data"):
        await open_meteo_client.historical_forecast(
            latitude=52.27,
            longitude=6.87417,
            start_date=date(2024, 1, 1),
            end_date=date(2024, 1, 1),
            pressure_level_variables=[PressureLevelVariable.TEMPERATURE],
            pressure_levels=[850],
            pressure_level_sections=[ForecastSection.CURRENT],
        )

    with pytest.raises(ValueError, match="There is no current data"):
        await open_meteo_client.single_run(
            latitude=52.27,
            longitude=6.87417,
            run=datetime(2026, 9, 1, tzinfo=ZoneInfo("UTC")),
            pressure_level_variables=[PressureLevelVariable.TEMPERATURE],
            pressure_levels=[850],
            pressure_level_sections=[ForecastSection.CURRENT],
        )


async def test_forecast_beyond_model_range(
    responses: aioresponses,
    open_meteo_client: OpenMeteo,
    snapshot: SnapshotAssertion,
) -> None:
    """Test values the weather models have no data for are None.

    The API allows a forecast of 16 days, but the weather models run out
    before the end of it. The fixture holds the tail of a real 16 day
    forecast, where the API returns null for those values.
    """
    mock_endpoint(responses, FORECAST_URL, "forecast_16_days.json")

    forecast = await open_meteo_client.forecast(
        latitude=52.27,
        longitude=6.87417,
        hourly=[
            HourlyParameters.TEMPERATURE_2M,
            HourlyParameters.WEATHER_CODE,
            HourlyParameters.IS_DAY,
        ],
        daily=[
            DailyParameters.TEMPERATURE_2M_MAX,
            DailyParameters.WEATHER_CODE,
            DailyParameters.SUNRISE,
        ],
        forecast_days=16,
    )

    assert forecast.hourly is not None
    assert forecast.hourly.temperature_2m == [None, None, None, None]
    assert forecast.daily is not None
    assert forecast.daily.temperature_2m_max == [18.3, None]
    assert forecast == snapshot


async def test_historical_forecast(
    responses: aioresponses,
    open_meteo_client: OpenMeteo,
    snapshot: SnapshotAssertion,
) -> None:
    """Test requesting forecasts the weather models made in the past."""
    mock_endpoint(responses, HISTORICAL_FORECAST_URL, "historical_forecast.json")

    forecast = await open_meteo_client.historical_forecast(
        latitude=52.27,
        longitude=6.87417,
        timezone="Europe/Amsterdam",
        start_date=date(2024, 1, 1),
        end_date=date(2024, 1, 2),
        hourly=[HourlyParameters.TEMPERATURE_2M, HourlyParameters.WEATHER_CODE],
        daily=[DailyParameters.TEMPERATURE_2M_MAX, DailyParameters.PRECIPITATION_SUM],
    )

    # Only what was asked for; the forecast defaults like past_days don't apply
    assert requested_query(responses) == {
        "daily": "temperature_2m_max,precipitation_sum",
        "end_date": "2024-01-02",
        "hourly": "temperature_2m,weather_code",
        "latitude": "52.27",
        "longitude": "6.87417",
        "precipitation_unit": "mm",
        "start_date": "2024-01-01",
        "temperature_unit": "celsius",
        "timeformat": "iso8601",
        "timezone": "Europe/Amsterdam",
        "wind_speed_unit": "kmh",
    }
    assert forecast.daily is not None
    assert forecast.daily.time == [date(2024, 1, 1), date(2024, 1, 2)]
    assert forecast == snapshot


async def test_historical_forecast_models(
    responses: aioresponses,
    open_meteo_client: OpenMeteo,
) -> None:
    """Test models and pressure levels work the same as for the forecast."""
    mock_endpoint(
        responses,
        HISTORICAL_FORECAST_URL,
        "forecast_pressure_levels_models.json",
    )

    forecast = await open_meteo_client.historical_forecast(
        latitude=52.27,
        longitude=6.87417,
        start_date=date(2024, 1, 1),
        end_date=date(2024, 1, 1),
        hourly=[HourlyParameters.TEMPERATURE_2M],
        pressure_level_variables=[PressureLevelVariable.TEMPERATURE],
        pressure_levels=[850],
        models=["icon_seamless", "gfs_seamless"],
    )

    assert "temperature_850hPa" in requested_query(responses)["hourly"]
    assert forecast.models is not None
    gfs = forecast.models["gfs_seamless"].hourly
    assert gfs is not None
    assert gfs.pressure_levels is not None


async def test_historical_weather(
    responses: aioresponses,
    open_meteo_client: OpenMeteo,
    snapshot: SnapshotAssertion,
) -> None:
    """Test requesting the historical weather.

    The fixture is a real response for the North Sea flood of 1953.
    """
    mock_endpoint(responses, HISTORICAL_WEATHER_URL, "historical_weather.json")

    weather = await open_meteo_client.historical_weather(
        latitude=52.27,
        longitude=6.87417,
        timezone="Europe/Amsterdam",
        start_date=date(1953, 1, 31),
        end_date=date(1953, 2, 1),
        hourly=[
            HourlyParameters.TEMPERATURE_2M,
            HourlyParameters.WIND_SPEED_10M,
            HourlyParameters.SOIL_MOISTURE_INDEX_0_TO_7CM,
        ],
        daily=[DailyParameters.WIND_GUSTS_10M_MAX, DailyParameters.PRECIPITATION_SUM],
    )

    query = requested_query(responses)
    assert query["start_date"] == "1953-01-31"
    assert query["end_date"] == "1953-02-01"
    assert "past_days" not in query
    assert weather.daily is not None
    assert weather.daily.wind_gusts_10m_max is not None
    assert weather.hourly is not None
    assert weather.hourly.soil_moisture_index_0_to_7cm is not None
    assert weather == snapshot


async def test_historical_weather_best_match(
    responses: aioresponses,
    open_meteo_client: OpenMeteo,
) -> None:
    """Test best_match data ends up under the name it was requested by.

    The archive suffixes the data of best_match as archive_best_match, which
    also ends in _best_match.
    """
    mock_endpoint(responses, HISTORICAL_WEATHER_URL, "historical_weather_models.json")

    weather = await open_meteo_client.historical_weather(
        latitude=52.27,
        longitude=6.87417,
        start_date=date(2024, 1, 1),
        end_date=date(2024, 1, 1),
        daily=[DailyParameters.TEMPERATURE_2M_MAX],
        models=["best_match", "era5", "era5_land"],
    )

    assert requested_query(responses)["models"] == "best_match,era5,era5_land"
    assert weather.daily is None
    assert weather.models is not None
    assert list(weather.models) == ["best_match", "era5", "era5_land"]
    best_match = weather.models["best_match"].daily
    assert best_match is not None
    assert best_match.temperature_2m_max == [8.0]


async def test_marine(
    responses: aioresponses,
    open_meteo_client: OpenMeteo,
    snapshot: SnapshotAssertion,
) -> None:
    """Test requesting every marine variable, for a location in the North Sea."""
    mock_endpoint(responses, MARINE_URL, "marine.json")

    marine = await open_meteo_client.marine(
        latitude=53.0,
        longitude=4.0,
        timezone="Europe/Amsterdam",
        current=list(MarineParameters),
        minutely_15=list(MarineParameters),
        hourly=list(MarineParameters),
        daily=list(MarineDailyParameters),
        forecast_days=3,
        forecast_minutely_15=3,
    )

    query = requested_query(responses)
    assert query["hourly"] == ",".join(MarineParameters)
    assert query["daily"] == ",".join(MarineDailyParameters)
    assert query["length_unit"] == "metric"
    assert "past_days" not in query

    assert marine.current is not None
    assert marine.current.wave_height is not None
    assert marine.current_units is not None
    assert marine.current_units.wave_height == "m"
    assert marine.minutely_15 is not None
    assert marine.hourly is not None
    assert marine.daily is not None
    assert marine.daily.wave_height_max is not None
    assert marine == snapshot


async def test_marine_options(
    responses: aioresponses,
    open_meteo_client: OpenMeteo,
) -> None:
    """Test the marine units and time range options end up in the query."""
    mock_endpoint(responses, MARINE_URL, "marine.json")

    await open_meteo_client.marine(
        latitude=53.0,
        longitude=4.0,
        start_date=date(2026, 10, 4),
        end_date=date(2026, 10, 5),
        temporal_resolution=TemporalResolution.HOURLY_3,
        cell_selection=CellSelection.SEA,
        length_unit=LengthUnit.IMPERIAL,
        temperature_unit=TemperatureUnit.FAHRENHEIT,
        wind_speed_unit=WindSpeedUnit.KNOTS,
    )

    query = requested_query(responses)
    assert query["start_date"] == "2026-10-04"
    assert query["end_date"] == "2026-10-05"
    assert query["temporal_resolution"] == "hourly_3"
    assert query["cell_selection"] == "sea"
    assert query["length_unit"] == "imperial"
    assert query["temperature_unit"] == "fahrenheit"
    assert query["wind_speed_unit"] == "kn"


async def test_marine_models(
    responses: aioresponses,
    open_meteo_client: OpenMeteo,
) -> None:
    """Test the data of each marine model ends up in a response of its own.

    The marine API suffixes the data of best_match as marine_best_match,
    which also ends in _best_match.
    """
    mock_endpoint(responses, MARINE_URL, "marine_models.json")

    models = ["best_match", "ecmwf_wam025", "ncep_gfswave025"]
    marine = await open_meteo_client.marine(
        latitude=53.0,
        longitude=4.0,
        hourly=[MarineParameters.WAVE_HEIGHT],
        models=models,
    )

    assert marine.hourly is None
    assert marine.models is not None
    assert list(marine.models) == models
    best_match = marine.models["best_match"].hourly
    ecmwf = marine.models["ecmwf_wam025"].hourly
    assert best_match is not None
    assert ecmwf is not None
    assert best_match.wave_height is not None
    assert best_match.wave_height != ecmwf.wave_height


async def test_flood(
    responses: aioresponses,
    open_meteo_client: OpenMeteo,
    snapshot: SnapshotAssertion,
) -> None:
    """Test requesting the river discharge of the Rhine, entering the Netherlands."""
    mock_endpoint(responses, FLOOD_URL, "flood.json")

    flood = await open_meteo_client.flood(
        latitude=51.84,
        longitude=6.11,
        daily=list(FloodParameters),
        forecast_days=3,
    )

    query = requested_query(responses)
    assert query["daily"] == ",".join(FloodParameters)
    assert query["forecast_days"] == "3"
    # Only sent when asked for
    assert "ensemble" not in query

    assert flood.daily is not None
    assert flood.daily.river_discharge is not None
    assert flood.daily.members is None
    assert flood.daily_units is not None
    assert flood.daily_units.river_discharge == "m³/s"
    assert flood == snapshot


async def test_flood_ensemble_with_models(
    responses: aioresponses,
    open_meteo_client: OpenMeteo,
) -> None:
    """Test ensemble members are grouped per member, and per model.

    With multiple models, the API suffixes the members with the model as
    well, like river_discharge_member01_seamless_v4. The flood API suffixes
    the data of best_match as flood_best_match.
    """
    mock_endpoint(responses, FLOOD_URL, "flood_ensemble_models.json")

    flood = await open_meteo_client.flood(
        latitude=51.84,
        longitude=6.11,
        daily=[FloodParameters.RIVER_DISCHARGE],
        ensemble=True,
        models=["best_match", "seamless_v4"],
    )

    query = requested_query(responses)
    assert query["ensemble"] == "true"
    assert query["models"] == "best_match,seamless_v4"

    assert flood.daily is None
    assert flood.models is not None
    daily = flood.models["best_match"].daily
    assert daily is not None
    assert daily.river_discharge is not None
    assert daily.members is not None
    assert list(daily.members) == list(range(1, 51))
    member = daily.members[1]
    assert member.time == daily.time
    assert member.river_discharge is not None
    assert member.members is None

    units = flood.models["best_match"].daily_units
    assert units is not None
    assert units.river_discharge == "m³/s"


async def test_climate(
    responses: aioresponses,
    open_meteo_client: OpenMeteo,
    snapshot: SnapshotAssertion,
) -> None:
    """Test requesting climate projections for 2050."""
    mock_endpoint(responses, CLIMATE_URL, "climate.json")

    climate = await open_meteo_client.climate(
        latitude=52.27,
        longitude=6.87417,
        start_date=date(2050, 7, 1),
        end_date=date(2050, 7, 3),
        daily=[DailyParameters.TEMPERATURE_2M_MAX, DailyParameters.PRECIPITATION_SUM],
        models=["MRI_AGCM3_2_S"],
        disable_bias_correction=True,
    )

    query = requested_query(responses)
    assert query["start_date"] == "2050-07-01"
    assert query["end_date"] == "2050-07-03"
    assert query["models"] == "MRI_AGCM3_2_S"
    assert query["disable_bias_correction"] == "true"

    assert climate.daily is not None
    assert climate.daily.time == [date(2050, 7, 1), date(2050, 7, 2), date(2050, 7, 3)]
    assert climate.daily.temperature_2m_max is not None
    assert climate == snapshot


async def test_climate_models(
    responses: aioresponses,
    open_meteo_client: OpenMeteo,
) -> None:
    """Test the data of each climate model ends up in a response of its own."""
    mock_endpoint(responses, CLIMATE_URL, "climate_models.json")

    climate = await open_meteo_client.climate(
        latitude=52.27,
        longitude=6.87417,
        start_date=date(2050, 7, 1),
        end_date=date(2050, 7, 3),
        daily=[DailyParameters.TEMPERATURE_2M_MAX, DailyParameters.PRECIPITATION_SUM],
        models=["MRI_AGCM3_2_S", "MPI_ESM1_2_XR"],
        precipitation_unit=PrecipitationUnit.INCHES,
    )

    query = requested_query(responses)
    assert query["precipitation_unit"] == "inch"
    # Only sent when asked for
    assert "disable_bias_correction" not in query

    assert climate.models is not None
    mri = climate.models["MRI_AGCM3_2_S"].daily
    mpi = climate.models["MPI_ESM1_2_XR"].daily
    assert mri is not None
    assert mpi is not None
    assert mri.temperature_2m_max != mpi.temperature_2m_max
    units = climate.models["MRI_AGCM3_2_S"].daily_units
    assert units is not None
    assert units.precipitation_sum == "inch"


async def test_climate_best_match_with_other_models(
    open_meteo_client: OpenMeteo,
) -> None:
    """Test best_match can't be combined with other climate models.

    The climate API returns best_match data under the name of the model it
    picked, so there is no telling it apart.
    """
    with pytest.raises(ValueError, match="best_match can't be combined"):
        await open_meteo_client.climate(
            latitude=52.27,
            longitude=6.87417,
            start_date=date(2050, 7, 1),
            end_date=date(2050, 7, 1),
            daily=[DailyParameters.TEMPERATURE_2M_MAX],
            models=["best_match", "MPI_ESM1_2_XR"],
        )


async def test_ensemble(
    responses: aioresponses,
    open_meteo_client: OpenMeteo,
    snapshot: SnapshotAssertion,
) -> None:
    """Test ensemble members are grouped per member, with their pressure levels.

    The API suffixes pressure level variables with the member as well, like
    temperature_850hPa_member01.
    """
    mock_endpoint(responses, ENSEMBLE_URL, "ensemble.json")

    forecast = await open_meteo_client.ensemble(
        latitude=52.27,
        longitude=6.87417,
        models=["cmc_gem_geps"],
        hourly=[HourlyParameters.TEMPERATURE_2M],
        pressure_level_variables=[PressureLevelVariable.TEMPERATURE],
        pressure_levels=[850],
        daily=[DailyParameters.TEMPERATURE_2M_MAX],
        forecast_days=1,
    )

    query = requested_query(responses)
    assert query["models"] == "cmc_gem_geps"
    assert query["hourly"] == "temperature_2m,temperature_850hPa"

    hourly = forecast.hourly
    assert hourly is not None
    assert hourly.temperature_2m is not None
    assert hourly.pressure_levels is not None
    assert hourly.members is not None
    assert list(hourly.members) == list(range(1, 21))
    member = hourly.members[20]
    assert member.time == hourly.time
    assert member.temperature_2m is not None
    assert member.temperature_2m != hourly.temperature_2m
    assert member.pressure_levels is not None
    assert member.pressure_levels[850].temperature is not None

    assert forecast.daily is not None
    assert forecast.daily.members is not None
    assert len(forecast.daily.members) == 20

    assert forecast.hourly_units is not None
    assert forecast.hourly_units.pressure_levels is not None
    assert forecast.hourly_units.pressure_levels[850].temperature == "°C"
    assert forecast == snapshot


async def test_ensemble_models(
    responses: aioresponses,
    open_meteo_client: OpenMeteo,
) -> None:
    """Test ensemble members are grouped per model as well.

    icon_seamless is an older name, which the API returns as
    icon_seamless_eps; its data ends up under the requested name.
    """
    mock_endpoint(responses, ENSEMBLE_URL, "ensemble_models.json")

    forecast = await open_meteo_client.ensemble(
        latitude=52.27,
        longitude=6.87417,
        models=["icon_seamless", "ecmwf_ifs025_ensemble"],
        hourly=[HourlyParameters.TEMPERATURE_2M],
    )

    assert forecast.hourly is None
    assert forecast.models is not None
    icon = forecast.models["icon_seamless"].hourly
    ecmwf = forecast.models["ecmwf_ifs025_ensemble"].hourly
    assert icon is not None
    assert ecmwf is not None
    assert icon.members is not None
    assert ecmwf.members is not None
    assert len(icon.members) == 39
    assert len(ecmwf.members) == 50


async def test_ensemble_spread(
    responses: aioresponses,
    open_meteo_client: OpenMeteo,
    snapshot: SnapshotAssertion,
) -> None:
    """Test the spread of an ensemble mean model, with its pressure levels."""
    mock_endpoint(responses, ENSEMBLE_URL, "ensemble_spread.json")

    forecast = await open_meteo_client.ensemble(
        latitude=52.27,
        longitude=6.87417,
        models=["ecmwf_ifs025_ensemble_mean"],
        current=[HourlyParameters.TEMPERATURE_2M],
        hourly=[HourlyParameters.TEMPERATURE_2M, HourlyParameters.WEATHER_CODE],
        pressure_level_variables=[PressureLevelVariable.TEMPERATURE],
        pressure_levels=[850],
        spread=True,
    )

    # The API has no spread for the weather code
    query = requested_query(responses)
    assert query["hourly"] == (
        "temperature_2m,weather_code,temperature_850hPa,"
        "temperature_2m_spread,temperature_850hPa_spread"
    )
    assert query["current"] == "temperature_2m,temperature_2m_spread"

    hourly = forecast.hourly
    assert hourly is not None
    assert hourly.spread is not None
    assert hourly.spread.time == hourly.time
    assert hourly.spread.temperature_2m is not None
    assert hourly.spread.weather_code is None
    assert hourly.spread.pressure_levels is not None
    assert hourly.spread.pressure_levels[850].temperature is not None

    assert forecast.current is not None
    assert forecast.current.spread is not None
    assert forecast.current.spread.temperature_2m is not None

    # The spread of a temperature in °C is in K
    assert forecast.hourly_units is not None
    assert forecast.hourly_units.temperature_2m == "°C"
    assert forecast.hourly_units.spread is not None
    assert forecast.hourly_units.spread.temperature_2m == "K"
    assert forecast.hourly_units.spread.pressure_levels is not None
    assert forecast.hourly_units.spread.pressure_levels[850].temperature == "K"
    assert forecast.current_units is not None
    assert forecast.current_units.spread is not None
    assert forecast.current_units.spread.temperature_2m == "K"
    assert forecast == snapshot


async def test_ensemble_without_spread(
    responses: aioresponses,
    open_meteo_client: OpenMeteo,
) -> None:
    """Test the spread is only requested when asked for."""
    mock_endpoint(responses, ENSEMBLE_URL, "ensemble.json")

    await open_meteo_client.ensemble(
        latitude=52.27,
        longitude=6.87417,
        models=["cmc_gem_geps"],
        hourly=[HourlyParameters.TEMPERATURE_2M],
    )

    assert "_spread" not in requested_query(responses)["hourly"]


async def test_seasonal(
    responses: aioresponses,
    open_meteo_client: OpenMeteo,
    snapshot: SnapshotAssertion,
) -> None:
    """Test requesting a seasonal forecast, with every kind of section."""
    mock_endpoint(responses, SEASONAL_URL, "seasonal.json")

    seasonal = await open_meteo_client.seasonal(
        latitude=52.27,
        longitude=6.87417,
        hourly=[HourlyParameters.TEMPERATURE_2M],
        daily=[DailyParameters.TEMPERATURE_2M_MAX],
        weekly=[
            SeasonalWeeklyParameters.TEMPERATURE_2M_MEAN,
            SeasonalWeeklyParameters.TEMPERATURE_2M_ANOMALY,
            SeasonalWeeklyParameters.TEMPERATURE_2M_ANOMALY_GT1,
            SeasonalWeeklyParameters.TEMPERATURE_2M_EFI,
        ],
        monthly=[
            SeasonalMonthlyParameters.TEMPERATURE_2M_MEAN,
            SeasonalMonthlyParameters.PRECIPITATION_ANOMALY,
        ],
        models=["ecmwf_seasonal_seamless"],
        forecast_days=31,
    )

    query = requested_query(responses)
    assert query["weekly"] == (
        "temperature_2m_mean,temperature_2m_anomaly,"
        "temperature_2m_anomaly_gt1,temperature_2m_efi"
    )
    assert query["monthly"] == "temperature_2m_mean,precipitation_anomaly"

    # The 6-hourly and daily data have the ensemble members
    assert seasonal.hourly is not None
    assert seasonal.hourly.members is not None
    assert len(seasonal.hourly.members) == 50
    assert seasonal.daily is not None
    assert seasonal.daily.members is not None

    # The weekly and monthly data are statistics over the members
    assert seasonal.weekly is not None
    assert seasonal.weekly.temperature_2m_anomaly_gt1 is not None
    assert seasonal.weekly_units is not None
    assert seasonal.weekly_units.temperature_2m_anomaly_gt1 == "%"
    assert seasonal.monthly is not None
    assert seasonal.monthly.time == [date(2026, 10, 1)]
    assert seasonal.monthly.precipitation_anomaly is not None
    assert seasonal == snapshot


async def test_seasonal_models(
    responses: aioresponses,
    open_meteo_client: OpenMeteo,
) -> None:
    """Test each model has the weekly or monthly data it provides.

    Weekly data comes from EC46, monthly data from SEAS5.
    """
    mock_endpoint(responses, SEASONAL_URL, "seasonal_models.json")

    seasonal = await open_meteo_client.seasonal(
        latitude=52.27,
        longitude=6.87417,
        daily=[DailyParameters.TEMPERATURE_2M_MAX],
        weekly=[SeasonalWeeklyParameters.TEMPERATURE_2M_ANOMALY],
        monthly=[SeasonalMonthlyParameters.TEMPERATURE_2M_MEAN],
        models=["ecmwf_seas5", "ecmwf_ec46"],
    )

    assert seasonal.models is not None
    seas5 = seasonal.models["ecmwf_seas5"]
    ec46 = seasonal.models["ecmwf_ec46"]
    assert seas5.weekly is None
    assert seas5.monthly is not None
    assert ec46.weekly is not None
    assert ec46.monthly is None
    assert seas5.daily is not None
    assert seas5.daily.members is not None


async def test_seasonal_best_match_with_other_models(
    open_meteo_client: OpenMeteo,
) -> None:
    """Test best_match can't be combined with other seasonal models."""
    with pytest.raises(ValueError, match="best_match can't be combined"):
        await open_meteo_client.seasonal(
            latitude=52.27,
            longitude=6.87417,
            daily=[DailyParameters.TEMPERATURE_2M_MAX],
            models=["best_match", "ecmwf_seas5"],
        )


async def test_previous_runs(
    responses: aioresponses,
    open_meteo_client: OpenMeteo,
    snapshot: SnapshotAssertion,
) -> None:
    """Test earlier model runs are grouped by how many days earlier they ran."""
    mock_endpoint(responses, PREVIOUS_RUNS_URL, "previous_runs.json")

    forecast = await open_meteo_client.previous_runs(
        latitude=52.27,
        longitude=6.87417,
        previous_days=[1, 2],
        current=[HourlyParameters.TEMPERATURE_2M],
        hourly=[HourlyParameters.TEMPERATURE_2M, HourlyParameters.PRECIPITATION],
        past_days=1,
        forecast_days=1,
    )

    # Every variable is requested for every previous day as well
    query = requested_query(responses)
    assert query["current"] == (
        "temperature_2m,temperature_2m_previous_day1,temperature_2m_previous_day2"
    )
    assert query["hourly"] == (
        "temperature_2m,precipitation,"
        "temperature_2m_previous_day1,temperature_2m_previous_day2,"
        "precipitation_previous_day1,precipitation_previous_day2"
    )

    assert forecast.current is not None
    assert forecast.current.previous_days is not None
    assert list(forecast.current.previous_days) == [1, 2]
    assert forecast.current.previous_days[1].interval == forecast.current.interval

    hourly = forecast.hourly
    assert hourly is not None
    assert hourly.previous_days is not None
    assert list(hourly.previous_days) == [1, 2]
    earlier = hourly.previous_days[2]
    assert earlier.time == hourly.time
    assert earlier.temperature_2m is not None
    assert earlier.temperature_2m != hourly.temperature_2m
    assert earlier.previous_days is None

    assert forecast.current_units is not None
    assert forecast.current_units.temperature_2m == "°C"
    assert forecast == snapshot


async def test_previous_runs_models(
    responses: aioresponses,
    open_meteo_client: OpenMeteo,
) -> None:
    """Test earlier model runs are grouped per model as well.

    With multiple models, the API suffixes the previous day with the model,
    like temperature_2m_previous_day1_icon_seamless.
    """
    mock_endpoint(responses, PREVIOUS_RUNS_URL, "previous_runs_models.json")

    forecast = await open_meteo_client.previous_runs(
        latitude=52.27,
        longitude=6.87417,
        previous_days=[1],
        hourly=[HourlyParameters.TEMPERATURE_2M],
        models=["icon_seamless", "gfs_seamless"],
    )

    assert forecast.models is not None
    icon = forecast.models["icon_seamless"].hourly
    assert icon is not None
    assert icon.previous_days is not None
    assert icon.previous_days[1].temperature_2m is not None


async def test_single_run(
    responses: aioresponses,
    open_meteo_client: OpenMeteo,
    snapshot: SnapshotAssertion,
) -> None:
    """Test requesting the forecast of a specific model run."""
    mock_endpoint(responses, SINGLE_RUN_URL, "single_run.json")

    forecast = await open_meteo_client.single_run(
        latitude=52.27,
        longitude=6.87417,
        # Naive on purpose: a naive run is taken as UTC
        run=datetime(2026, 9, 1, 0, 0),  # noqa: DTZ001
        hourly=[HourlyParameters.TEMPERATURE_2M],
        daily=[DailyParameters.TEMPERATURE_2M_MAX],
        models=["ecmwf_ifs"],
        forecast_days=2,
    )

    query = requested_query(responses)
    assert query["run"] == "2026-09-01T00:00"
    assert query["forecast_days"] == "2"
    # These don't apply to a single run
    assert "past_days" not in query
    assert "start_date" not in query

    # The data starts at the start of the run
    assert forecast.hourly is not None
    assert forecast.hourly.time[0] == datetime(2026, 9, 1, 0, 0)  # noqa: DTZ001
    assert forecast.daily is not None
    assert forecast.daily.time == [date(2026, 9, 1), date(2026, 9, 2)]
    assert forecast == snapshot


async def test_single_run_timezone_aware(
    responses: aioresponses,
    open_meteo_client: OpenMeteo,
) -> None:
    """Test a timezone aware run is converted to UTC, as the API expects."""
    mock_endpoint(responses, SINGLE_RUN_URL, "single_run.json")

    await open_meteo_client.single_run(
        latitude=52.27,
        longitude=6.87417,
        run=datetime(2026, 9, 1, 14, 0, tzinfo=ZoneInfo("Europe/Amsterdam")),
        hourly=[HourlyParameters.TEMPERATURE_2M],
    )

    assert requested_query(responses)["run"] == "2026-09-01T12:00"


async def test_satellite_radiation(
    responses: aioresponses,
    open_meteo_client: OpenMeteo,
    snapshot: SnapshotAssertion,
) -> None:
    """Test requesting solar radiation measured by satellites."""
    mock_endpoint(responses, SATELLITE_URL, "satellite_radiation.json")

    satellite = await open_meteo_client.satellite_radiation(
        latitude=52.27,
        longitude=6.87417,
        timezone="Europe/Amsterdam",
        start_date=date(2026, 9, 30),
        end_date=date(2026, 9, 30),
        # Naive on purpose: the API reads these as local time in the timezone
        start_hour=datetime(2026, 9, 30, 12, 0),  # noqa: DTZ001
        end_hour=datetime(2026, 9, 30, 14, 0),  # noqa: DTZ001
        hourly=[
            HourlyParameters.SHORTWAVE_RADIATION,
            HourlyParameters.SHORTWAVE_RADIATION_CLEAR_SKY,
            HourlyParameters.GLOBAL_TILTED_IRRADIANCE,
        ],
        daily=[
            DailyParameters.SHORTWAVE_RADIATION_SUM,
            DailyParameters.SUNSHINE_DURATION,
        ],
        tilt=35,
        azimuth=0,
    )

    # Without a model, the API serves its regular archive instead
    query = requested_query(responses)
    assert query["models"] == "satellite_radiation_seamless"
    assert query["tilt"] == "35"

    assert satellite.hourly is not None
    assert satellite.hourly.shortwave_radiation is not None
    assert satellite.hourly.shortwave_radiation_clear_sky is not None
    assert satellite.daily is not None
    assert satellite.daily.shortwave_radiation_sum is not None
    assert satellite == snapshot


async def test_satellite_radiation_model(
    responses: aioresponses,
    open_meteo_client: OpenMeteo,
) -> None:
    """Test a specific satellite data source replaces the default one."""
    mock_endpoint(responses, SATELLITE_URL, "satellite_radiation.json")

    await open_meteo_client.satellite_radiation(
        latitude=52.27,
        longitude=6.87417,
        past_days=2,
        hourly=[HourlyParameters.SHORTWAVE_RADIATION],
        temporal_resolution=TemporalResolution.NATIVE,
        models=["eumetsat_sarah3"],
    )

    query = requested_query(responses)
    assert query["models"] == "eumetsat_sarah3"
    assert query["past_days"] == "2"
    assert query["temporal_resolution"] == "native"


async def test_satellite_radiation_not_covered(
    responses: aioresponses,
    open_meteo_client: OpenMeteo,
) -> None:
    """Test a location outside the coverage raises, instead of failing to parse.

    The API returns NaN coordinates for those, like for New York, which isn't
    valid JSON; hence the fixture is a plain text file.
    """
    mock_endpoint(responses, SATELLITE_URL, "satellite_radiation_not_covered.txt")

    with pytest.raises(OpenMeteoError, match="outside the area the API covers"):
        await open_meteo_client.satellite_radiation(
            latitude=40.71,
            longitude=-74.0,
            hourly=[HourlyParameters.SHORTWAVE_RADIATION],
        )


async def test_air_quality(
    responses: aioresponses,
    open_meteo_client: OpenMeteo,
    snapshot: SnapshotAssertion,
) -> None:
    """Test requesting every air quality variable."""
    mock_endpoint(responses, AIR_QUALITY_URL, "air_quality.json")

    air_quality = await open_meteo_client.air_quality(
        latitude=52.27,
        longitude=6.87417,
        timezone="Europe/Amsterdam",
        current=list(AirQualityParameters),
        hourly=list(AirQualityParameters),
    )

    assert requested_query(responses) == {
        "current": ",".join(AirQualityParameters),
        "hourly": ",".join(AirQualityParameters),
        "latitude": "52.27",
        "longitude": "6.87417",
        "past_days": "0",
        "timeformat": "iso8601",
        "timezone": "Europe/Amsterdam",
    }
    assert air_quality == snapshot


async def test_air_quality_defaults(
    responses: aioresponses,
    open_meteo_client: OpenMeteo,
) -> None:
    """Test anything left unset is left out of the query."""
    mock_endpoint(responses, AIR_QUALITY_URL, "air_quality.json")

    await open_meteo_client.air_quality(latitude=52.27, longitude=6.87417)

    query = requested_query(responses)
    assert "current" not in query
    assert "forecast_days" not in query
    assert "hourly" not in query


async def test_air_quality_forecast_days(
    responses: aioresponses,
    open_meteo_client: OpenMeteo,
) -> None:
    """Test the number of forecast days ends up in the query."""
    mock_endpoint(responses, AIR_QUALITY_URL, "air_quality.json")

    await open_meteo_client.air_quality(
        latitude=52.27,
        longitude=6.87417,
        forecast_days=3,
    )

    assert requested_query(responses)["forecast_days"] == "3"


async def test_air_quality_options(
    responses: aioresponses,
    open_meteo_client: OpenMeteo,
) -> None:
    """Test the air quality time range and model options end up in the query."""
    mock_endpoint(responses, AIR_QUALITY_URL, "air_quality.json")

    await open_meteo_client.air_quality(
        latitude=52.27,
        longitude=6.87417,
        start_date=date(2026, 10, 4),
        end_date=date(2026, 10, 5),
        # Naive on purpose: the API reads these as local time in the timezone
        start_hour=datetime(2026, 10, 4, 6, 0),  # noqa: DTZ001
        end_hour=datetime(2026, 10, 4, 18, 0),  # noqa: DTZ001
        forecast_hours=6,
        past_hours=2,
        temporal_resolution=TemporalResolution.HOURLY_3,
        domains=AirQualityDomain.CAMS_EUROPE,
        cell_selection=CellSelection.NEAREST,
    )

    query = requested_query(responses)
    assert query["start_date"] == "2026-10-04"
    assert query["end_date"] == "2026-10-05"
    assert query["start_hour"] == "2026-10-04T06:00"
    assert query["end_hour"] == "2026-10-04T18:00"
    assert query["forecast_hours"] == "6"
    assert query["past_hours"] == "2"
    assert query["temporal_resolution"] == "hourly_3"
    assert query["domains"] == "cams_europe"
    assert query["cell_selection"] == "nearest"


async def test_geocoding(
    responses: aioresponses,
    open_meteo_client: OpenMeteo,
    snapshot: SnapshotAssertion,
) -> None:
    """Test searching for a location."""
    mock_endpoint(responses, GEOCODING_URL, "geocoding.json")

    geocoding = await open_meteo_client.geocoding(
        name="Enschede",
        count=2,
    )

    assert requested_query(responses) == {
        "count": "2",
        "format": "json",
        "language": "en",
        "name": "Enschede",
    }
    assert geocoding == snapshot


async def test_geocoding_country_code(
    responses: aioresponses,
    open_meteo_client: OpenMeteo,
) -> None:
    """Test the country filter is sent in the camelCase the API expects."""
    mock_endpoint(responses, GEOCODING_URL, "geocoding.json")

    await open_meteo_client.geocoding(name="Enschede", country_code="NL")

    query = requested_query(responses)
    assert query["countryCode"] == "NL"
    assert "country_code" not in query


async def test_geocoding_by_id(
    responses: aioresponses,
    open_meteo_client: OpenMeteo,
    snapshot: SnapshotAssertion,
) -> None:
    """Test getting a single location by its ID."""
    mock_endpoint(responses, GEOCODING_BY_ID_URL, "geocoding_by_id.json")

    location = await open_meteo_client.geocoding_by_id(
        location_id=2756071,
        language="nl",
    )

    assert requested_query(responses) == {
        "format": "json",
        "id": "2756071",
        "language": "nl",
    }
    assert location.geo_id == 2756071
    assert location.name == "Enschede"
    assert location.country == "Nederland"
    assert location == snapshot


async def test_geocoding_by_id_unknown(
    responses: aioresponses,
    open_meteo_client: OpenMeteo,
) -> None:
    """Test an unknown location ID raises with the reason the API gives."""
    responses.get(
        re.compile(rf"^{re.escape(GEOCODING_BY_ID_URL)}\?.*$"),
        status=400,
        body='{"reason":"Location ID not found.","error":true}',
        content_type="application/json",
    )

    with pytest.raises(OpenMeteoError, match="Location ID not found"):
        await open_meteo_client.geocoding_by_id(location_id=1)


async def test_geocoding_no_results(
    responses: aioresponses,
    open_meteo_client: OpenMeteo,
) -> None:
    """Test the API leaves out results entirely when nothing matches."""
    mock_endpoint(responses, GEOCODING_URL, "geocoding_empty.json")

    geocoding = await open_meteo_client.geocoding(name="Xyzzyplughnowhere")

    assert geocoding.results is None


async def test_geocoding_missing_fields(
    responses: aioresponses,
    open_meteo_client: OpenMeteo,
    snapshot: SnapshotAssertion,
) -> None:
    """Test results without a country or elevation still parse.

    The fixture holds three real results, taken from searches for
    Antarctica, McMurdo, and Atlantic.
    """
    mock_endpoint(responses, GEOCODING_URL, "geocoding_missing_fields.json")

    geocoding = await open_meteo_client.geocoding(name="Antarctica")

    assert geocoding.results is not None
    antarctica, island, cape = geocoding.results
    assert antarctica.country is None
    assert antarctica.country_code is None
    assert antarctica.country_id is None
    assert island.country is None
    assert island.country_code is not None
    assert cape.elevation is None
    assert geocoding == snapshot


async def test_elevation(
    responses: aioresponses,
    open_meteo_client: OpenMeteo,
    snapshot: SnapshotAssertion,
) -> None:
    """Test looking up the elevation of a location."""
    mock_endpoint(responses, ELEVATION_URL, "elevation.json")

    elevation = await open_meteo_client.elevation(latitude=52.27, longitude=6.87417)

    assert requested_query(responses) == {
        "latitude": "52.27",
        "longitude": "6.87417",
    }
    assert elevation.elevation == [29.0]
    assert elevation == snapshot


async def test_elevation_multiple_coordinates(
    responses: aioresponses,
    open_meteo_client: OpenMeteo,
) -> None:
    """Test looking up the elevation of multiple locations at once."""
    responses.get(
        re.compile(rf"^{re.escape(ELEVATION_URL)}\?.*$"),
        status=200,
        body='{"elevation":[29.0,46.0]}',
        content_type="application/json",
    )

    elevation = await open_meteo_client.elevation(
        latitude=[52.27, 48.85],
        longitude=[6.87417, 2.35],
    )

    assert requested_query(responses) == {
        "latitude": "52.27,48.85",
        "longitude": "6.87417,2.35",
    }
    assert elevation.elevation == [29.0, 46.0]


async def test_timeout(
    responses: aioresponses,
    open_meteo_client: OpenMeteo,
) -> None:
    """Test a timeout is raised as a connection error."""
    responses.get("http://example.com/api/", exception=TimeoutError())

    with pytest.raises(OpenMeteoConnectionError, match="Timeout occurred"):
        await open_meteo_client._request(URL("http://example.com/api/"))


async def test_client_error(
    responses: aioresponses,
    open_meteo_client: OpenMeteo,
) -> None:
    """Test a client error is raised as a connection error."""
    responses.get("http://example.com/api/", exception=aiohttp.ClientError())

    with pytest.raises(OpenMeteoConnectionError, match="Error occurred"):
        await open_meteo_client._request(URL("http://example.com/api/"))


async def test_api_error_with_reason(
    responses: aioresponses,
    open_meteo_client: OpenMeteo,
) -> None:
    """Test the reason the API gives is passed on in the error."""
    # The exact body the API returns for an out of range latitude
    responses.get(
        "http://example.com/api/",
        status=400,
        body=(
            '{"reason":"Latitude must be in range of -90 to 90°. '
            'Given: 999.0.","error":true}'
        ),
        content_type="application/json",
    )

    with pytest.raises(OpenMeteoError, match="Latitude must be in range"):
        await open_meteo_client._request(URL("http://example.com/api/"))


async def test_api_error_without_reason(
    responses: aioresponses,
    open_meteo_client: OpenMeteo,
) -> None:
    """Test a JSON error without a reason still raises."""
    responses.get(
        "http://example.com/api/",
        status=500,
        body='{"status":"nok"}',
        content_type="application/json",
    )

    with pytest.raises(OpenMeteoResponseError) as error:
        await open_meteo_client._request(URL("http://example.com/api/"))

    assert error.value.status == 500
    assert error.value.reason == 'HTTP 500: {"status":"nok"}'


async def test_http_error_plain_text(
    responses: aioresponses,
    open_meteo_client: OpenMeteo,
) -> None:
    """Test a non-JSON error response raises with the body as message."""
    responses.get(
        "http://example.com/api/",
        status=404,
        body="OMG PUPPIES!",
        content_type="text/plain",
    )

    with pytest.raises(OpenMeteoResponseError) as error:
        await open_meteo_client._request(URL("http://example.com/api/"))

    assert error.value.status == 404
    assert error.value.reason == "HTTP 404: OMG PUPPIES!"


async def test_unexpected_content_type(
    responses: aioresponses,
    open_meteo_client: OpenMeteo,
) -> None:
    """Test a successful response that is not JSON raises."""
    responses.get(
        "http://example.com/api/",
        status=200,
        body="<html>Not JSON</html>",
        content_type="text/html",
    )

    with pytest.raises(OpenMeteoError, match="Unexpected response"):
        await open_meteo_client._request(URL("http://example.com/api/"))


class _StallingResponse:
    """A response that sends its headers, but fails while reading the body."""

    def __init__(self, body_error: BaseException | None) -> None:
        """Fail reading the body with this error, or stall when it is None."""
        self.status = 200
        self.headers = {"Content-Type": "application/json"}
        self._body_error = body_error

    async def __aenter__(self) -> Self:
        """Enter the response context."""
        return self

    async def __aexit__(self, *_exc_info: object) -> None:
        """Release the response."""

    async def read(self) -> bytes:
        """Stall, or fail, while reading the body."""
        if self._body_error is not None:
            raise self._body_error
        await asyncio.sleep(10)
        return b"{}"


class _StallingSession:  # pylint: disable=too-few-public-methods
    """A session that returns a response failing while reading its body."""

    def __init__(self, body_error: BaseException | None = None) -> None:
        """Fail reading the body with this error, or stall when it is None."""
        self._body_error = body_error

    def get(self, _url: URL) -> _StallingResponse:
        """Return the response, which only fails once its body is read."""
        return _StallingResponse(self._body_error)


async def test_timeout_while_reading_body() -> None:
    """Test a body that stalls after the headers counts toward the timeout."""
    open_meteo = OpenMeteo(
        request_timeout=0.1,
        session=cast("aiohttp.ClientSession", _StallingSession()),
    )

    with pytest.raises(OpenMeteoConnectionError, match="Timeout occurred"):
        await open_meteo._request(URL("http://example.com/api/"))


async def test_connection_error_while_reading_body() -> None:
    """Test a body that breaks off is raised as a connection error."""
    open_meteo = OpenMeteo(
        session=cast(
            "aiohttp.ClientSession",
            _StallingSession(aiohttp.ClientPayloadError("broken off")),
        ),
    )

    with pytest.raises(OpenMeteoConnectionError, match="Error occurred"):
        await open_meteo._request(URL("http://example.com/api/"))


async def test_api_error_status(
    responses: aioresponses,
    open_meteo_client: OpenMeteo,
) -> None:
    """Test an API error has the status and the reason the API gave."""
    responses.get(
        "http://example.com/api/",
        status=400,
        body='{"reason":"Latitude must be in range of -90 to 90°.","error":true}',
        content_type="application/json",
    )

    with pytest.raises(OpenMeteoResponseError) as error:
        await open_meteo_client._request(URL("http://example.com/api/"))

    assert error.value.status == 400
    assert error.value.reason == "Latitude must be in range of -90 to 90°."
    assert str(error.value) == "Latitude must be in range of -90 to 90°."


@pytest.mark.parametrize(
    ("headers", "retry_after"),
    [
        ({"Retry-After": "60"}, 60),
        ({}, None),
        # A date instead of seconds is allowed, but not worth parsing
        ({"Retry-After": "Wed, 21 Oct 2026 07:28:00 GMT"}, None),
    ],
)
async def test_rate_limit(
    responses: aioresponses,
    open_meteo_client: OpenMeteo,
    headers: dict[str, str],
    retry_after: int | None,
) -> None:
    """Test a rate limited request raises with how long to wait, if known."""
    responses.get(
        "http://example.com/api/",
        status=429,
        body='{"reason":"Daily API request limit exceeded.","error":true}',
        content_type="application/json",
        headers=headers,
    )

    with pytest.raises(OpenMeteoRateLimitError) as error:
        await open_meteo_client._request(URL("http://example.com/api/"))

    assert error.value.status == 429
    assert error.value.reason == "Daily API request limit exceeded."
    assert error.value.retry_after == retry_after


@pytest.mark.parametrize(
    "body",
    [
        "null",
        # A proxy in between can respond with HTML, marked as JSON
        "<html>Bad Gateway</html>",
    ],
)
async def test_api_error_without_reason_object(
    responses: aioresponses,
    open_meteo_client: OpenMeteo,
    body: str,
) -> None:
    """Test a JSON error without a reason object still raises with the status."""
    responses.get(
        "http://example.com/api/",
        status=502,
        body=body,
        content_type="application/json",
    )

    with pytest.raises(OpenMeteoResponseError) as error:
        await open_meteo_client._request(URL("http://example.com/api/"))

    assert error.value.status == 502
    assert error.value.reason == f"HTTP 502: {body}"


@pytest.mark.parametrize(
    "body",
    [
        "not json",
        # Valid JSON, but missing the fields every response has
        "{}",
    ],
)
async def test_unexpected_response_body(
    responses: aioresponses,
    open_meteo_client: OpenMeteo,
    body: str,
) -> None:
    """Test a response that doesn't fit the models raises an OpenMeteoError."""
    mock_endpoint_body(responses, GEOCODING_URL, body)

    with pytest.raises(OpenMeteoError, match="Unexpected response"):
        await open_meteo_client.geocoding(name="Enschede")


async def test_unexpected_response_body_with_models(
    responses: aioresponses,
    open_meteo_client: OpenMeteo,
) -> None:
    """Test invalid JSON raises an OpenMeteoError when splitting models too."""
    mock_endpoint_body(responses, FORECAST_URL, "not json")

    with pytest.raises(OpenMeteoError, match="Unexpected response"):
        await open_meteo_client.forecast(
            latitude=52.27,
            longitude=6.87417,
            models=["icon_seamless", "gfs_seamless"],
        )


def mock_endpoint_body(responses: aioresponses, url: str, body: str) -> None:
    """Mock an endpoint with a raw body, regardless of the query string sent."""
    responses.get(
        re.compile(rf"^{re.escape(url)}\?.*$"),
        status=200,
        body=body,
        content_type="application/json",
    )
