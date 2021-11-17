"""Asynchronous client for the Open-Meteo API."""
from __future__ import annotations

import asyncio
import socket
from dataclasses import dataclass
from typing import Any

import async_timeout
from aiohttp.client import ClientError, ClientResponseError, ClientSession
from yarl import URL

from .exceptions import OpenMeteoConnectionError, OpenMeteoError
from .models import (
    DailyParameters,
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

    async def _request(self, url: URL) -> dict[str, Any]:
        """Handle a request to the Open-Meteo API.

        A generic method for sending/handling HTTP requests done against
        the public Open-Meteo API.

        Args:
            url: URL to call.

        Returns:
            A Python dictionary (JSON decoded) with the response from
            the API.

        Raises:
            OpenMeteoConnectionError: An error occurred while communicating with
                the Open-Meteo API.
            OpenMeteoError: Received an unexpected response from the Open-Meteo
                API.
        """
        if self.session is None:
            self.session = ClientSession()
            self._close_session = True

        try:
            async with async_timeout.timeout(self.request_timeout):
                response = await self.session.get(url)
        except asyncio.TimeoutError as exception:
            raise OpenMeteoConnectionError(
                "Timeout occurred while connecting to the Open-Meteo API"
            ) from exception
        except (
            ClientError,
            ClientResponseError,
            socket.gaierror,
        ) as exception:
            raise OpenMeteoConnectionError(
                "Error occurred while communicating with Open-Meteo API"
            ) from exception
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

        if "application/json" not in content_type:
            text = await response.text()
            raise OpenMeteoError(
                "Unexpected response from the Open-Meteo API",
                {"Content-Type": content_type, "response": text},
            )

        return await response.json()

    async def forecast(
        self,
        *,
        latitude: float,
        longitude: float,
        timezone: str = "UTC",
        current_weather: bool = False,
        daily: list[DailyParameters] | None = None,
        hourly: list[HourlyParameters] | None = None,
        past_days: int = 0,
        precipitation_unit: PrecipitationUnit = PrecipitationUnit.MILLIMETERS,
        temperature_unit: TemperatureUnit = TemperatureUnit.CELSIUS,
        timeformat: TimeFormat = TimeFormat.ISO_8601,
        wind_speed_unit: WindSpeedUnit = WindSpeedUnit.KILOMETERS_PER_HOUR,
    ) -> Forecast:
        """Get weather forecast.

        Args:
            latitude: Latitude of the location.
            longitude: Longitude of the location.
            current_weather: Include current weather conditions.
            daily: A list of weather variables to query for.
            hourly: A list of weather variables to query for.
            past_days: If set, yesterdays or the day before yesterdays are also
                returned (0-2).
            precipitation_unit: Precipitation unit.
            temperature_unit: Temperature unit.
            timeformat: Timeformat.
            timezone: All timestamps are returned as local-time and data is
                returned starting at 0:00 local-time.
            wind_speed_unit: Wind speed unit.

        Returns:
            A forecast object.
        """
        url = URL("https://api.open-meteo.com/v1/forecast").with_query(
            current_weather="true" if current_weather else "false",
            daily=",".join(daily) if daily is not None else [],
            hourly=",".join(hourly) if hourly is not None else [],
            latitude=latitude,
            longitude=longitude,
            past_days=past_days,
            precipitation_unit=precipitation_unit,
            temperature_unit=temperature_unit,
            timeformat=timeformat,
            timezone=timezone,
            windspeed_unit=wind_speed_unit,
        )
        data = await self._request(url=url)
        return Forecast.parse_obj(data)

    async def geocoding(
        self,
        *,
        name: str,
        count: int = 10,
        language: str = "en",
    ) -> Geocoding:
        """Get geocoding result.

        Args:
            name: String to search for. An empty string or only 1 character
                will return an empty resultset. 2 characters will only match
                exact matching locations. 3 and more locations will perform
                fuzzy matching. The search string can be a location name or
                a postal code.
            count: The number of search results to return. Up up 100 results
                can be retrieved.
            language: Return translated results, if available, otherwise return
                english or the native location name. Lower-cased.

        Returns:
            An Geocoding object.
        """
        url = URL("https://geocoding-api.open-meteo.com/v1/search").with_query(
            name=name,
            count=count,
            format="json",
            language=language,
        )
        data = await self._request(url=url)
        return Geocoding.parse_obj(data)

    async def close(self) -> None:
        """Close open client session."""
        if self.session and self._close_session:
            await self.session.close()

    async def __aenter__(self) -> OpenMeteo:
        """Async enter.

        Returns:
            The OpenMeteo object.
        """
        return self

    async def __aexit__(self, *_exc_info) -> None:
        """Async exit.

        Args:
            _exc_info: Exec type.
        """
        await self.close()
