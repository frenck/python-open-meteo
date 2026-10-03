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
    AirQualityParameters,
    CellSelection,
    DailyParameters,
    HourlyParameters,
    OpenMeteo,
    PrecipitationUnit,
    TemperatureUnit,
    TemporalResolution,
    TimeFormat,
    WindSpeedUnit,
)
from open_meteo.exceptions import OpenMeteoConnectionError, OpenMeteoError

from .conftest import load_fixture

FORECAST_URL = "https://api.open-meteo.com/v1/forecast"
AIR_QUALITY_URL = "https://air-quality-api.open-meteo.com/v1/air-quality"
GEOCODING_URL = "https://geocoding-api.open-meteo.com/v1/search"
ELEVATION_URL = "https://api.open-meteo.com/v1/elevation"


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
    assert query["precipitation_unit"] == "in"
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
