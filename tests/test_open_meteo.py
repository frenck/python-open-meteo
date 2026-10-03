"""Tests for the Open-Meteo client."""

# pylint: disable=protected-access

import re
from datetime import date, datetime
from urllib.parse import unquote

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
    HourlyParameters,
    LengthUnit,
    MarineDailyParameters,
    MarineParameters,
    OpenMeteo,
    PrecipitationUnit,
    PressureLevelVariable,
    TemperatureUnit,
    TemporalResolution,
    TimeFormat,
    WindSpeedUnit,
)
from open_meteo.exceptions import OpenMeteoConnectionError, OpenMeteoError

from .conftest import load_fixture

FORECAST_URL = "https://api.open-meteo.com/v1/forecast"
HISTORICAL_FORECAST_URL = "https://historical-forecast-api.open-meteo.com/v1/forecast"
HISTORICAL_WEATHER_URL = "https://archive-api.open-meteo.com/v1/archive"
AIR_QUALITY_URL = "https://air-quality-api.open-meteo.com/v1/air-quality"
GEOCODING_URL = "https://geocoding-api.open-meteo.com/v1/search"
GEOCODING_BY_ID_URL = "https://geocoding-api.open-meteo.com/v1/get"
ELEVATION_URL = "https://api.open-meteo.com/v1/elevation"
MARINE_URL = "https://marine-api.open-meteo.com/v1/marine"


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
        timeformat=TimeFormat.UNIXTIME,
        wind_speed_unit=WindSpeedUnit.KNOTS,
    )

    query = requested_query(responses)
    assert query["forecast_days"] == "1"
    assert query["past_days"] == "1"
    assert query["precipitation_unit"] == "inch"
    assert query["temperature_unit"] == "fahrenheit"
    assert query["timeformat"] == "unixtime"
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

    with pytest.raises(OpenMeteoError) as error:
        await open_meteo_client._request(URL("http://example.com/api/"))

    assert error.value.args == (500, {"status": "nok"})


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

    with pytest.raises(OpenMeteoError) as error:
        await open_meteo_client._request(URL("http://example.com/api/"))

    assert error.value.args == (404, {"message": "OMG PUPPIES!"})


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
