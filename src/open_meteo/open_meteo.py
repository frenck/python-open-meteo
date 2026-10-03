"""Asynchronous client for the Open-Meteo API."""

from __future__ import annotations

import asyncio
import socket
from dataclasses import dataclass
from typing import Self

from aiohttp.client import ClientError, ClientResponseError, ClientSession
from yarl import URL

from .exceptions import OpenMeteoConnectionError, OpenMeteoError
from .models import (
    AirQuality,
    AirQualityParameters,
    DailyParameters,
    Elevation,
    Forecast,
    Geocoding,
    HourlyParameters,
    PrecipitationUnit,
    TemperatureUnit,
    TimeFormat,
    WindSpeedUnit,
)


@dataclass
class OpenMeteo:
    """Main class for the Open-Meteo API."""

    # Request timeout in seconds.
    request_timeout: float = 10.0

    # Custom client session to use for requests.
    session: ClientSession | None = None

    _close_session: bool = False

    async def _request(self, url: URL) -> str:
        """Handle a request to the Open-Meteo API.

        A generic method for sending/handling HTTP requests done against
        the public Open-Meteo API.

        Args:
        ----
            url: URL to call.

        Returns:
        -------
            A Python dictionary (JSON decoded) with the response from
            the API.

        Raises:
        ------
            OpenMeteoConnectionError: An error occurred while communicating with
                the Open-Meteo API.
            OpenMeteoError: Received an unexpected response from the Open-Meteo
                API.

        """
        if self.session is None:
            self.session = ClientSession()
            self._close_session = True

        try:
            async with asyncio.timeout(self.request_timeout):
                response = await self.session.get(url)
        except TimeoutError as exception:
            msg = "Timeout occurred while connecting to the Open-Meteo API"
            raise OpenMeteoConnectionError(msg) from exception
        except (
            ClientError,
            ClientResponseError,
            socket.gaierror,
        ) as exception:
            msg = "Error occurred while communicating with Open-Meteo API"
            raise OpenMeteoConnectionError(msg) from exception
        content_type = response.headers.get("Content-Type", "")
        if (response.status // 100) in [4, 5]:
            if "application/json" in content_type:
                data = await response.json()
                response.close()
                if data.get("error") is True and (reason := data.get("reason")):
                    raise OpenMeteoError(reason)
                raise OpenMeteoError(response.status, data)
            contents = await response.read()
            response.close()
            raise OpenMeteoError(response.status, {"message": contents.decode("utf8")})

        text = await response.text()
        if "application/json" not in content_type:
            msg = "Unexpected response from the Open-Meteo API"
            raise OpenMeteoError(
                msg,
                {"Content-Type": content_type, "response": text},
            )

        return text

    # pylint: disable-next=too-many-arguments
    async def forecast(  # noqa: PLR0913
        self,
        *,
        latitude: float,
        longitude: float,
        timezone: str = "UTC",
        current: list[HourlyParameters] | None = None,
        daily: list[DailyParameters] | None = None,
        hourly: list[HourlyParameters] | None = None,
        forecast_days: int | None = None,
        past_days: int = 0,
        precipitation_unit: PrecipitationUnit = PrecipitationUnit.MILLIMETERS,
        temperature_unit: TemperatureUnit = TemperatureUnit.CELSIUS,
        timeformat: TimeFormat = TimeFormat.ISO_8601,
        wind_speed_unit: WindSpeedUnit = WindSpeedUnit.KILOMETERS_PER_HOUR,
    ) -> Forecast:
        """Get weather forecast.

        Args:
        ----
            latitude: Latitude of the location.
            longitude: Longitude of the location.
            timezone: All timestamps are returned as local time and data is
                returned starting at 0:00 local time.
            current: A list of weather variables to get the current
                conditions for. Every hourly variable is available.
            daily: A list of daily weather variables to query for.
            hourly: A list of hourly weather variables to query for.
            forecast_days: Number of days to forecast (0-16). Leave unset for
                the API default of 7 days.
            past_days: Number of past days to include as well.
            precipitation_unit: Precipitation unit.
            temperature_unit: Temperature unit.
            timeformat: Format of the returned timestamps.
            wind_speed_unit: Wind speed unit.

        Returns:
        -------
            A Forecast object.

        """
        url = URL("https://api.open-meteo.com/v1/forecast").with_query(
            current=",".join(current) if current is not None else [],
            daily=",".join(daily) if daily is not None else [],
            hourly=",".join(hourly) if hourly is not None else [],
            forecast_days=forecast_days if forecast_days is not None else [],
            latitude=latitude,
            longitude=longitude,
            past_days=past_days,
            precipitation_unit=precipitation_unit,
            temperature_unit=temperature_unit,
            timeformat=timeformat,
            timezone=timezone,
            wind_speed_unit=wind_speed_unit,
        )
        data = await self._request(url=url)
        return Forecast.from_json(data)

    # pylint: disable-next=too-many-arguments
    async def air_quality(  # noqa: PLR0913
        self,
        *,
        latitude: float,
        longitude: float,
        timezone: str = "UTC",
        current: list[AirQualityParameters] | None = None,
        hourly: list[AirQualityParameters] | None = None,
        forecast_days: int | None = None,
        past_days: int = 0,
        timeformat: TimeFormat = TimeFormat.ISO_8601,
    ) -> AirQuality:
        """Get air quality forecast.

        Args:
        ----
            latitude: Latitude of the location.
            longitude: Longitude of the location.
            timezone: All timestamps are returned as local time and data is
                returned starting at 0:00 local time.
            current: A list of air quality variables to get the current
                conditions for.
            hourly: A list of hourly air quality variables to query for.
            forecast_days: Number of days to forecast (0-7). Leave unset for
                the API default of 5 days.
            past_days: Number of past days to include as well.
            timeformat: Format of the returned timestamps.

        Returns:
        -------
            An AirQuality object.

        """
        url = URL("https://air-quality-api.open-meteo.com/v1/air-quality").with_query(
            current=",".join(current) if current is not None else [],
            hourly=",".join(hourly) if hourly is not None else [],
            forecast_days=forecast_days if forecast_days is not None else [],
            latitude=latitude,
            longitude=longitude,
            past_days=past_days,
            timeformat=timeformat,
            timezone=timezone,
        )
        data = await self._request(url=url)
        return AirQuality.from_json(data)

    async def geocoding(
        self,
        *,
        name: str,
        count: int = 10,
        language: str = "en",
    ) -> Geocoding:
        """Get geocoding result.

        Args:
        ----
            name: String to search for. An empty string or only 1 character
                will return an empty result set. 2 characters will only match
                exact matching locations. 3 and more characters will perform
                fuzzy matching. The search string can be a location name or
                a postal code.
            count: The number of search results to return. Up to 100 results
                can be retrieved.
            language: Return translated results, if available, otherwise return
                English or the native location name. Lower-cased.

        Returns:
        -------
            A Geocoding object.

        """
        url = URL("https://geocoding-api.open-meteo.com/v1/search").with_query(
            name=name,
            count=count,
            format="json",
            language=language,
        )
        data = await self._request(url=url)
        return Geocoding.from_json(data)

    async def elevation(
        self,
        *,
        latitude: float,
        longitude: float,
    ) -> Elevation:
        """Get elevation above sea level for a coordinate.

        Args:
        ----
            latitude: Latitude of the location.
            longitude: Longitude of the location.

        Returns:
        -------
            An Elevation object containing the elevation in meters. This is
            always a list, holding a single value for a single coordinate.

        """
        url = URL("https://api.open-meteo.com/v1/elevation").with_query(
            latitude=latitude,
            longitude=longitude,
        )
        data = await self._request(url=url)
        return Elevation.from_json(data)

    async def close(self) -> None:
        """Close open client session."""
        if self.session and self._close_session:
            await self.session.close()

    async def __aenter__(self) -> Self:
        """Async enter.

        Returns
        -------
            The OpenMeteo object.

        """
        return self

    async def __aexit__(self, *_exc_info: object) -> None:
        """Async exit.

        Args:
        ----
            _exc_info: Exec type.

        """
        await self.close()
