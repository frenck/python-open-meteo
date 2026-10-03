"""Asynchronous client for the Open-Meteo API."""

from __future__ import annotations

import asyncio
import socket
from dataclasses import dataclass
from datetime import date, datetime
from typing import Any, Self, TypeVar

import orjson
from aiohttp.client import ClientError, ClientResponseError, ClientSession
from mashumaro.mixins.orjson import DataClassORJSONMixin
from yarl import URL

from .exceptions import OpenMeteoConnectionError, OpenMeteoError
from .models import (
    AirQuality,
    AirQualityDomain,
    AirQualityParameters,
    CellSelection,
    DailyParameters,
    Elevation,
    Flood,
    FloodParameters,
    Forecast,
    Geocoding,
    GeocodingResult,
    HourlyParameters,
    LengthUnit,
    Marine,
    MarineDailyParameters,
    MarineParameters,
    PrecipitationUnit,
    PressureLevelVariable,
    Seasonal,
    SeasonalMonthlyParameters,
    SeasonalWeeklyParameters,
    TemperatureUnit,
    TemporalResolution,
    TimeFormat,
    WindSpeedUnit,
)

ResponseT = TypeVar("ResponseT", bound=DataClassORJSONMixin)


def _build_query(**parameters: object) -> dict[str, str]:
    """Build a query string, the way the Open-Meteo API expects it.

    Parameters that are not set are left out, so the API defaults apply.
    Lists become comma separated, booleans lowercase, and dates and times use
    ISO 8601. Floats are formatted here, as yarl refuses NaN, which the API
    uses to switch off elevation downscaling.
    """
    query: dict[str, str] = {}
    for key, value in parameters.items():
        if value is None:
            continue

        # A datetime is a date as well, so it has to be checked first
        if isinstance(value, list):
            query[key] = ",".join(str(item) for item in value)
        elif isinstance(value, bool):
            query[key] = "true" if value else "false"
        elif isinstance(value, datetime):
            query[key] = value.strftime("%Y-%m-%dT%H:%M")
        elif isinstance(value, date):
            query[key] = value.isoformat()
        else:
            query[key] = str(value)

    return query


# Response sections that get a model suffix when multiple models are requested;
# the current conditions always come from a single model and never do
MODEL_SECTIONS = (
    "minutely_15",
    "minutely_15_units",
    "hourly",
    "hourly_units",
    "daily",
    "daily_units",
    "weekly",
    "weekly_units",
    "monthly",
    "monthly_units",
)


def _split_models(
    data: dict[str, Any],
    models: list[str],
    suffixes: dict[str, str] | None = None,
) -> dict[str, Any]:
    """Split a multiple model response into a response per model.

    With multiple models, the API suffixes every variable with the model name,
    exactly as it was requested: temperature_2m becomes
    temperature_2m_icon_seamless. This moves each model's data into a response
    of its own, under the models key, with the suffixes removed, so it parses
    into the regular models.

    When only one of the requested models has data for the location, the API
    leaves out the suffixes, and there is no telling which model the data is
    from. The response is returned as is then, like a single model response.

    Some APIs use another suffix than the requested name for a model; suffixes
    maps those requested names to the suffix the API uses.
    """
    # Match on the suffix the API uses, but keep the data under the name the
    # model was requested by
    suffix_to_model = {(suffixes or {}).get(model, model): model for model in models}

    # The longest suffix has to win: temperature_2m_meteoswiss_icon_seamless
    # also ends in _icon_seamless
    by_length = sorted(suffix_to_model, key=str.__len__, reverse=True)
    shared = {key: value for key, value in data.items() if key not in MODEL_SECTIONS}

    # Keep the models in the order they were requested
    per_model: dict[str, dict[str, Any]] = {
        model: dict(shared) for model in dict.fromkeys(models)
    }

    split = False
    for section in MODEL_SECTIONS:
        if section not in data:
            continue

        leftover: dict[str, Any] = {}
        for key, value in data[section].items():
            suffix = next((m for m in by_length if key.endswith(f"_{m}")), None)

            # Time is shared between the models; anything else without a
            # model suffix stays where it is
            if suffix is None:
                leftover[key] = value
                continue

            model_section = per_model[suffix_to_model[suffix]].setdefault(section, {})
            model_section[key.removesuffix(f"_{suffix}")] = value
            split = True

        for model in per_model.values():
            if section in model and "time" in leftover:
                model[section]["time"] = leftover["time"]

        # Only keep the section on the top level, if more than time is left
        if set(leftover) - {"time"}:
            shared[section] = leftover

    if not split:
        return data

    # The current conditions are not per model, so they stay on the top level
    for model in per_model.values():
        model.pop("current", None)
        model.pop("current_units", None)

    return {**shared, "models": per_model}


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

    # pylint: disable-next=too-many-arguments,too-many-locals
    async def forecast(  # noqa: PLR0913
        self,
        *,
        latitude: float,
        longitude: float,
        timezone: str = "UTC",
        current: list[HourlyParameters] | None = None,
        minutely_15: list[HourlyParameters] | None = None,
        hourly: list[HourlyParameters] | None = None,
        pressure_level_variables: list[PressureLevelVariable] | None = None,
        pressure_levels: list[int] | None = None,
        daily: list[DailyParameters] | None = None,
        forecast_days: int | None = None,
        past_days: int = 0,
        forecast_hours: int | None = None,
        past_hours: int | None = None,
        forecast_minutely_15: int | None = None,
        past_minutely_15: int | None = None,
        start_date: date | None = None,
        end_date: date | None = None,
        start_hour: datetime | None = None,
        end_hour: datetime | None = None,
        temporal_resolution: TemporalResolution | None = None,
        elevation: float | None = None,
        cell_selection: CellSelection | None = None,
        tilt: float | None = None,
        azimuth: float | None = None,
        models: list[str] | None = None,
        precipitation_unit: PrecipitationUnit = PrecipitationUnit.MILLIMETERS,
        temperature_unit: TemperatureUnit = TemperatureUnit.CELSIUS,
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
            minutely_15: A list of weather variables to get 15-minutely data
                for. Every hourly variable is available.
            hourly: A list of hourly weather variables to query for.
            pressure_level_variables: A list of hourly weather variables to
                query for on each of the pressure levels. They end up in
                hourly.pressure_levels, keyed by the pressure level.
            pressure_levels: The pressure levels in hPa to query the pressure
                level variables for, like 850 or 500. Which levels have data
                depends on the weather model, from 10 up to 1000 hPa; levels
                a model doesn't have return no data instead of an error.
            daily: A list of daily weather variables to query for.
            forecast_days: Number of days to forecast (0-16). Leave unset for
                the API default of 7 days.
            past_days: Number of past days to include as well.
            forecast_hours: Number of hourly steps to return from now on,
                instead of whole days.
            past_hours: Number of past hourly steps to include, instead of
                whole days.
            forecast_minutely_15: Number of 15-minutely steps to return from
                now on, instead of whole days.
            past_minutely_15: Number of past 15-minutely steps to include,
                instead of whole days.
            start_date: First day of the time interval to return. Use it
                together with end_date, instead of forecast_days.
            end_date: Last day of the time interval to return.
            start_hour: First hour of the time interval to return, for hourly
                and 15-minutely data. Use it together with end_hour. This is
                local time in the requested timezone; tzinfo is not used.
            end_hour: Last hour of the time interval to return.
            temporal_resolution: Aggregate hourly data into larger time steps,
                or use the native resolution of the weather model.
            elevation: Elevation used for statistical downscaling. Leave unset
                to use a digital elevation model, or pass float("nan") to
                switch downscaling off.
            cell_selection: How to match the location to a grid cell of the
                weather model.
            tilt: Tilt of a solar panel in degrees, for global tilted
                irradiance. 0 is horizontal, 90 is vertical.
            azimuth: Orientation of a solar panel in degrees, for global
                tilted irradiance. 0 is south, -90 is east, 90 is west.
            models: Weather models to use, by their Open-Meteo name, like
                "icon_seamless". Leave unset to let the API pick the best
                model for the location. With a single model, the data is on
                the forecast itself. With multiple models, the data of each
                model is in Forecast.models, keyed by the model name as given.
                The current conditions always come from a single model. When
                only one of the models has data for the location, the API
                returns it without telling which model it is from, and it is
                on the forecast itself, like with a single model.
            precipitation_unit: Precipitation unit.
            temperature_unit: Temperature unit.
            wind_speed_unit: Wind speed unit.

        Returns:
        -------
            A Forecast object.

        Raises:
        ------
            ValueError: Only one of pressure_level_variables and
                pressure_levels is given; nothing would be requested.

        """
        return await self._forecast(
            "https://api.open-meteo.com/v1/forecast",
            hourly=hourly,
            pressure_level_variables=pressure_level_variables,
            pressure_levels=pressure_levels,
            models=models,
            latitude=latitude,
            longitude=longitude,
            timezone=timezone,
            current=current,
            minutely_15=minutely_15,
            daily=daily,
            forecast_days=forecast_days,
            past_days=past_days,
            forecast_hours=forecast_hours,
            past_hours=past_hours,
            forecast_minutely_15=forecast_minutely_15,
            past_minutely_15=past_minutely_15,
            start_date=start_date,
            end_date=end_date,
            start_hour=start_hour,
            end_hour=end_hour,
            temporal_resolution=temporal_resolution,
            elevation=elevation,
            cell_selection=cell_selection,
            tilt=tilt,
            azimuth=azimuth,
            precipitation_unit=precipitation_unit,
            temperature_unit=temperature_unit,
            wind_speed_unit=wind_speed_unit,
        )

    # pylint: disable-next=too-many-arguments,too-many-locals
    async def historical_forecast(  # noqa: PLR0913
        self,
        *,
        latitude: float,
        longitude: float,
        start_date: date,
        end_date: date,
        timezone: str = "UTC",
        minutely_15: list[HourlyParameters] | None = None,
        hourly: list[HourlyParameters] | None = None,
        pressure_level_variables: list[PressureLevelVariable] | None = None,
        pressure_levels: list[int] | None = None,
        daily: list[DailyParameters] | None = None,
        start_hour: datetime | None = None,
        end_hour: datetime | None = None,
        temporal_resolution: TemporalResolution | None = None,
        elevation: float | None = None,
        cell_selection: CellSelection | None = None,
        tilt: float | None = None,
        azimuth: float | None = None,
        models: list[str] | None = None,
        precipitation_unit: PrecipitationUnit = PrecipitationUnit.MILLIMETERS,
        temperature_unit: TemperatureUnit = TemperatureUnit.CELSIUS,
        wind_speed_unit: WindSpeedUnit = WindSpeedUnit.KILOMETERS_PER_HOUR,
    ) -> Forecast:
        """Get the forecasts the weather models made in the past.

        The historical forecast API archives the weather forecasts as they were
        made, with the same variables and models as the forecast. Data goes
        back to 2016, but how far exactly depends on the weather model.

        Args:
        ----
            latitude: Latitude of the location.
            longitude: Longitude of the location.
            start_date: First day of the time interval to return.
            end_date: Last day of the time interval to return.
            timezone: All timestamps are returned as local time and data is
                returned starting at 0:00 local time.
            minutely_15: A list of weather variables to get 15-minutely data
                for. Every hourly variable is available.
            hourly: A list of hourly weather variables to query for.
            pressure_level_variables: A list of hourly weather variables to
                query for on each of the pressure levels. They end up in
                hourly.pressure_levels, keyed by the pressure level.
            pressure_levels: The pressure levels in hPa to query the pressure
                level variables for, like 850 or 500. Which levels have data
                depends on the weather model.
            daily: A list of daily weather variables to query for.
            start_hour: First hour to return, to narrow down the time interval
                for hourly and 15-minutely data. This is local time in the
                requested timezone; tzinfo is not used.
            end_hour: Last hour to return.
            temporal_resolution: Aggregate hourly data into larger time steps,
                or use the native resolution of the weather model.
            elevation: Elevation used for statistical downscaling. Leave unset
                to use a digital elevation model, or pass float("nan") to
                switch downscaling off.
            cell_selection: How to match the location to a grid cell of the
                weather model.
            tilt: Tilt of a solar panel in degrees, for global tilted
                irradiance. 0 is horizontal, 90 is vertical.
            azimuth: Orientation of a solar panel in degrees, for global
                tilted irradiance. 0 is south, -90 is east, 90 is west.
            models: Weather models to use, by their Open-Meteo name. Works the
                same as for the forecast.
            precipitation_unit: Precipitation unit.
            temperature_unit: Temperature unit.
            wind_speed_unit: Wind speed unit.

        Returns:
        -------
            A Forecast object.

        Raises:
        ------
            ValueError: Only one of pressure_level_variables and
                pressure_levels is given; nothing would be requested.

        """
        return await self._forecast(
            "https://historical-forecast-api.open-meteo.com/v1/forecast",
            hourly=hourly,
            pressure_level_variables=pressure_level_variables,
            pressure_levels=pressure_levels,
            models=models,
            latitude=latitude,
            longitude=longitude,
            start_date=start_date,
            end_date=end_date,
            timezone=timezone,
            minutely_15=minutely_15,
            daily=daily,
            start_hour=start_hour,
            end_hour=end_hour,
            temporal_resolution=temporal_resolution,
            elevation=elevation,
            cell_selection=cell_selection,
            tilt=tilt,
            azimuth=azimuth,
            precipitation_unit=precipitation_unit,
            temperature_unit=temperature_unit,
            wind_speed_unit=wind_speed_unit,
        )

    # pylint: disable-next=too-many-arguments,too-many-locals
    async def ensemble(  # noqa: PLR0913
        self,
        *,
        latitude: float,
        longitude: float,
        models: list[str],
        timezone: str = "UTC",
        current: list[HourlyParameters] | None = None,
        minutely_15: list[HourlyParameters] | None = None,
        hourly: list[HourlyParameters] | None = None,
        pressure_level_variables: list[PressureLevelVariable] | None = None,
        pressure_levels: list[int] | None = None,
        daily: list[DailyParameters] | None = None,
        forecast_days: int | None = None,
        past_days: int | None = None,
        forecast_hours: int | None = None,
        past_hours: int | None = None,
        start_date: date | None = None,
        end_date: date | None = None,
        start_hour: datetime | None = None,
        end_hour: datetime | None = None,
        temporal_resolution: TemporalResolution | None = None,
        elevation: float | None = None,
        cell_selection: CellSelection | None = None,
        tilt: float | None = None,
        azimuth: float | None = None,
        precipitation_unit: PrecipitationUnit = PrecipitationUnit.MILLIMETERS,
        temperature_unit: TemperatureUnit = TemperatureUnit.CELSIUS,
        wind_speed_unit: WindSpeedUnit = WindSpeedUnit.KILOMETERS_PER_HOUR,
    ) -> Forecast:
        """Get an ensemble forecast, with all members of the ensemble models.

        Ensemble models run the same forecast many times, with slightly
        different starting conditions, to show how certain a forecast is.
        The regular values are the control run; the other members are in
        the members of the hourly, 15-minutely, and daily data, keyed by
        member number. Pressure levels work per member as well.

        Args:
        ----
            latitude: Latitude of the location.
            longitude: Longitude of the location.
            models: Ensemble models to use, by their Open-Meteo name, like
                "ecmwf_ifs025_ensemble" or "dwd_icon_seamless_eps". There is no
                default; with multiple models, the data of each model is in
                Forecast.models.
            timezone: All timestamps are returned as local time and data is
                returned starting at 0:00 local time.
            current: A list of weather variables to get the current
                conditions for. These are not per member.
            minutely_15: A list of weather variables to get 15-minutely data
                for.
            hourly: A list of hourly weather variables to query for.
            pressure_level_variables: A list of hourly weather variables to
                query for on each of the pressure levels.
            pressure_levels: The pressure levels in hPa to query the pressure
                level variables for, like 850 or 500.
            daily: A list of daily weather variables to query for.
            forecast_days: Number of days to forecast (0-36). Leave unset for
                the API default of 7 days.
            past_days: Number of past days to include as well.
            forecast_hours: Number of hourly steps to return from now on,
                instead of whole days.
            past_hours: Number of past hourly steps to include, instead of
                whole days.
            start_date: First day of the time interval to return. Use it
                together with end_date, instead of forecast_days.
            end_date: Last day of the time interval to return.
            start_hour: First hour of the time interval to return, for hourly
                and 15-minutely data. Use it together with end_hour. This is
                local time in the requested timezone; tzinfo is not used.
            end_hour: Last hour of the time interval to return.
            temporal_resolution: Aggregate hourly data into larger time steps,
                or use the native resolution of the ensemble model.
            elevation: Elevation used for statistical downscaling. Leave unset
                to use a digital elevation model, or pass float("nan") to
                switch downscaling off.
            cell_selection: How to match the location to a grid cell of the
                ensemble model.
            tilt: Tilt of a solar panel in degrees, for global tilted
                irradiance. 0 is horizontal, 90 is vertical.
            azimuth: Orientation of a solar panel in degrees, for global
                tilted irradiance. 0 is south, -90 is east, 90 is west.
            precipitation_unit: Precipitation unit.
            temperature_unit: Temperature unit.
            wind_speed_unit: Wind speed unit.

        Returns:
        -------
            A Forecast object.

        Raises:
        ------
            ValueError: Only one of pressure_level_variables and
                pressure_levels is given; nothing would be requested.

        """
        return await self._forecast(
            "https://ensemble-api.open-meteo.com/v1/ensemble",
            hourly=hourly,
            pressure_level_variables=pressure_level_variables,
            pressure_levels=pressure_levels,
            models=models,
            # Older model names still work, but the API returns their data
            # under the current name of the model
            model_suffixes={
                "gem_global": "gem_global_ensemble",
                "gfs025": "ncep_gefs025",
                "gfs05": "ncep_gefs05",
                "gfs_seamless": "ncep_gefs_seamless",
                "icon_d2": "icon_d2_eps",
                "icon_eu": "icon_eu_eps",
                "icon_global": "icon_global_eps",
                "icon_seamless": "icon_seamless_eps",
            },
            latitude=latitude,
            longitude=longitude,
            timezone=timezone,
            current=current,
            minutely_15=minutely_15,
            daily=daily,
            forecast_days=forecast_days,
            past_days=past_days,
            forecast_hours=forecast_hours,
            past_hours=past_hours,
            start_date=start_date,
            end_date=end_date,
            start_hour=start_hour,
            end_hour=end_hour,
            temporal_resolution=temporal_resolution,
            elevation=elevation,
            cell_selection=cell_selection,
            tilt=tilt,
            azimuth=azimuth,
            precipitation_unit=precipitation_unit,
            temperature_unit=temperature_unit,
            wind_speed_unit=wind_speed_unit,
        )

    # pylint: disable-next=too-many-arguments,too-many-locals
    async def historical_weather(  # noqa: PLR0913
        self,
        *,
        latitude: float,
        longitude: float,
        start_date: date,
        end_date: date,
        timezone: str = "UTC",
        hourly: list[HourlyParameters] | None = None,
        daily: list[DailyParameters] | None = None,
        start_hour: datetime | None = None,
        end_hour: datetime | None = None,
        temporal_resolution: TemporalResolution | None = None,
        elevation: float | None = None,
        cell_selection: CellSelection | None = None,
        tilt: float | None = None,
        azimuth: float | None = None,
        models: list[str] | None = None,
        precipitation_unit: PrecipitationUnit = PrecipitationUnit.MILLIMETERS,
        temperature_unit: TemperatureUnit = TemperatureUnit.CELSIUS,
        wind_speed_unit: WindSpeedUnit = WindSpeedUnit.KILOMETERS_PER_HOUR,
    ) -> Forecast:
        """Get the historical weather, from reanalysis datasets back to 1940.

        The historical weather API combines weather observations and weather
        models into reanalysis datasets, like ERA5. These are the best
        estimate of the weather in the past. ERA5 becomes available with a
        delay of about five days; by default, the most recent days are filled
        in with ECMWF IFS data. There is no 15-minutely data, no current
        conditions, and no data on pressure levels.

        Args:
        ----
            latitude: Latitude of the location.
            longitude: Longitude of the location.
            start_date: First day of the time interval to return, from
                1940-01-01 on.
            end_date: Last day of the time interval to return.
            timezone: All timestamps are returned as local time and data is
                returned starting at 0:00 local time.
            hourly: A list of hourly weather variables to query for.
            daily: A list of daily weather variables to query for.
            start_hour: First hour to return, to narrow down the time interval
                for hourly data. This is local time in the requested
                timezone; tzinfo is not used.
            end_hour: Last hour to return.
            temporal_resolution: Aggregate hourly data into larger time steps,
                or use the native resolution of the dataset.
            elevation: Elevation used for statistical downscaling. Leave unset
                to use a digital elevation model, or pass float("nan") to
                switch downscaling off.
            cell_selection: How to match the location to a grid cell of the
                dataset.
            tilt: Tilt of a solar panel in degrees, for global tilted
                irradiance. 0 is horizontal, 90 is vertical.
            azimuth: Orientation of a solar panel in degrees, for global
                tilted irradiance. 0 is south, -90 is east, 90 is west.
            models: Reanalysis datasets to use, by their Open-Meteo name, like
                "era5" or "era5_land". Works the same as for the forecast.
            precipitation_unit: Precipitation unit.
            temperature_unit: Temperature unit.
            wind_speed_unit: Wind speed unit.

        Returns:
        -------
            A Forecast object, as the response has the same shape.

        """
        return await self._forecast(
            "https://archive-api.open-meteo.com/v1/archive",
            hourly=hourly,
            pressure_level_variables=None,
            pressure_levels=None,
            models=models,
            # The archive suffixes best_match data as archive_best_match
            model_suffixes={"best_match": "archive_best_match"},
            latitude=latitude,
            longitude=longitude,
            start_date=start_date,
            end_date=end_date,
            timezone=timezone,
            daily=daily,
            start_hour=start_hour,
            end_hour=end_hour,
            temporal_resolution=temporal_resolution,
            elevation=elevation,
            cell_selection=cell_selection,
            tilt=tilt,
            azimuth=azimuth,
            precipitation_unit=precipitation_unit,
            temperature_unit=temperature_unit,
            wind_speed_unit=wind_speed_unit,
        )

    # pylint: disable-next=too-many-arguments
    async def _forecast(  # noqa: PLR0913
        self,
        url: str,
        *,
        hourly: list[HourlyParameters] | None,
        pressure_level_variables: list[PressureLevelVariable] | None,
        pressure_levels: list[int] | None,
        models: list[str] | None,
        model_suffixes: dict[str, str] | None = None,
        **parameters: object,
    ) -> Forecast:
        """Request and parse a forecast, shared by the forecast-like APIs.

        These APIs all have the same parameters and responses, on another
        host. This handles what needs more than passing a parameter on: the
        pressure levels and the models.
        """
        if (pressure_level_variables is None) != (pressure_levels is None):
            msg = "Both pressure_level_variables and pressure_levels are needed"
            raise ValueError(msg)

        # The API takes pressure level data as one variable per level, like
        # temperature_850hPa, so every variable is combined with every level
        hourly_variables: list[str] = list(hourly or [])
        if pressure_level_variables and pressure_levels:
            hourly_variables += [
                f"{variable}_{level}hPa"
                for variable in pressure_level_variables
                for level in pressure_levels
            ]

        return await self._request_with_models(
            url,
            Forecast,
            models=models,
            model_suffixes=model_suffixes,
            hourly=hourly_variables or None,
            **parameters,
        )

    async def _request_with_models(
        self,
        url: str,
        response_type: type[ResponseT],
        *,
        models: list[str] | None,
        model_suffixes: dict[str, str] | None = None,
        **parameters: object,
    ) -> ResponseT:
        """Request data from an API with weather models, and parse it.

        With multiple models, the data of each model is split into a response
        of its own first; see _split_models.
        """
        # The models parse timestamps in ISO 8601, so never rely on the default
        query = _build_query(
            **parameters,
            models=models,
            timeformat=TimeFormat.ISO_8601,
        )
        data = await self._request(url=URL(url).with_query(query))

        if models is not None and len(set(models)) > 1:
            return response_type.from_dict(
                _split_models(orjson.loads(data), models, model_suffixes)
            )

        return response_type.from_json(data)

    # pylint: disable-next=too-many-arguments,too-many-locals
    async def marine(  # noqa: PLR0913
        self,
        *,
        latitude: float,
        longitude: float,
        timezone: str = "UTC",
        current: list[MarineParameters] | None = None,
        minutely_15: list[MarineParameters] | None = None,
        hourly: list[MarineParameters] | None = None,
        daily: list[MarineDailyParameters] | None = None,
        forecast_days: int | None = None,
        past_days: int | None = None,
        forecast_hours: int | None = None,
        past_hours: int | None = None,
        forecast_minutely_15: int | None = None,
        past_minutely_15: int | None = None,
        start_date: date | None = None,
        end_date: date | None = None,
        start_hour: datetime | None = None,
        end_hour: datetime | None = None,
        temporal_resolution: TemporalResolution | None = None,
        cell_selection: CellSelection | None = None,
        models: list[str] | None = None,
        length_unit: LengthUnit = LengthUnit.METRIC,
        temperature_unit: TemperatureUnit = TemperatureUnit.CELSIUS,
        wind_speed_unit: WindSpeedUnit = WindSpeedUnit.KILOMETERS_PER_HOUR,
    ) -> Marine:
        """Get the marine forecast: waves, swell, ocean currents, and sea level.

        Marine data is only available at sea; on land, all values are None.
        Which variables have data depends on the location and the marine
        model. Data goes back to 1940.

        Args:
        ----
            latitude: Latitude of the location.
            longitude: Longitude of the location.
            timezone: All timestamps are returned as local time and data is
                returned starting at 0:00 local time.
            current: A list of marine variables to get the current conditions
                for.
            minutely_15: A list of marine variables to get 15-minutely data
                for.
            hourly: A list of hourly marine variables to query for.
            daily: A list of daily marine variables to query for.
            forecast_days: Number of days to forecast (0-16). Leave unset for
                the API default of 7 days.
            past_days: Number of past days to include as well.
            forecast_hours: Number of hourly steps to return from now on,
                instead of whole days.
            past_hours: Number of past hourly steps to include, instead of
                whole days.
            forecast_minutely_15: Number of 15-minutely steps to return from
                now on, instead of whole days.
            past_minutely_15: Number of past 15-minutely steps to include,
                instead of whole days.
            start_date: First day of the time interval to return. Use it
                together with end_date, instead of forecast_days.
            end_date: Last day of the time interval to return.
            start_hour: First hour of the time interval to return, for hourly
                and 15-minutely data. Use it together with end_hour. This is
                local time in the requested timezone; tzinfo is not used.
            end_hour: Last hour of the time interval to return.
            temporal_resolution: Aggregate hourly data into larger time steps,
                or use the native resolution of the marine model.
            cell_selection: How to match the location to a grid cell of the
                marine model.
            models: Marine models to use, by their Open-Meteo name, like
                "ecmwf_wam025". Works the same as for the forecast: with
                multiple models, the data of each model is in Marine.models.
            length_unit: Unit for wave heights and sea level: meters or feet.
            temperature_unit: Temperature unit, for the sea surface
                temperature.
            wind_speed_unit: Speed unit, for the ocean current velocity.

        Returns:
        -------
            A Marine object.

        """
        return await self._request_with_models(
            "https://marine-api.open-meteo.com/v1/marine",
            Marine,
            models=models,
            # The marine API suffixes best_match data as marine_best_match
            model_suffixes={"best_match": "marine_best_match"},
            latitude=latitude,
            longitude=longitude,
            timezone=timezone,
            current=current,
            minutely_15=minutely_15,
            hourly=hourly,
            daily=daily,
            forecast_days=forecast_days,
            past_days=past_days,
            forecast_hours=forecast_hours,
            past_hours=past_hours,
            forecast_minutely_15=forecast_minutely_15,
            past_minutely_15=past_minutely_15,
            start_date=start_date,
            end_date=end_date,
            start_hour=start_hour,
            end_hour=end_hour,
            temporal_resolution=temporal_resolution,
            cell_selection=cell_selection,
            length_unit=length_unit,
            temperature_unit=temperature_unit,
            wind_speed_unit=wind_speed_unit,
        )

    # pylint: disable-next=too-many-arguments
    async def climate(  # noqa: PLR0913
        self,
        *,
        latitude: float,
        longitude: float,
        start_date: date,
        end_date: date,
        daily: list[DailyParameters],
        timezone: str = "UTC",
        disable_bias_correction: bool = False,
        cell_selection: CellSelection | None = None,
        models: list[str] | None = None,
        precipitation_unit: PrecipitationUnit = PrecipitationUnit.MILLIMETERS,
        temperature_unit: TemperatureUnit = TemperatureUnit.CELSIUS,
        wind_speed_unit: WindSpeedUnit = WindSpeedUnit.KILOMETERS_PER_HOUR,
    ) -> Forecast:
        """Get climate projections, from 1950 up to 2050.

        Climate projections come from high resolution climate models, and are
        downscaled to 10 km and bias corrected onto ERA5-Land by default.
        Climate models have uncertainties and biases: they are meant for long
        term trends, like the temperature anomaly over decades, not for the
        weather of a specific day. Only daily data is available, for a
        subset of the daily variables.

        Args:
        ----
            latitude: Latitude of the location.
            longitude: Longitude of the location.
            start_date: First day of the time interval to return, from
                1950-01-01 on.
            end_date: Last day of the time interval to return, up to
                2050-12-31.
            daily: A list of daily weather variables to query for.
            timezone: All timestamps are returned as local time and data is
                returned starting at 0:00 local time.
            disable_bias_correction: Return the raw climate model data,
                without downscaling and bias correction onto ERA5-Land.
            cell_selection: How to match the location to a grid cell of the
                climate model.
            models: Climate models to use, by their exact, case sensitive
                Open-Meteo name, like "EC_Earth3P_HR" or "MRI_AGCM3_2_S".
                Works the same as for the forecast, except that best_match
                can't be combined with other models.
            precipitation_unit: Precipitation unit.
            temperature_unit: Temperature unit.
            wind_speed_unit: Wind speed unit.

        Returns:
        -------
            A Forecast object, as the response has the same shape.

        Raises:
        ------
            ValueError: best_match is combined with other models.

        """
        # The climate API returns best_match data under the name of the model
        # it picked for the location, so there is no telling it apart
        if models is not None and "best_match" in models and len(set(models)) > 1:
            msg = "best_match can't be combined with other climate models"
            raise ValueError(msg)

        return await self._request_with_models(
            "https://climate-api.open-meteo.com/v1/climate",
            Forecast,
            models=models,
            latitude=latitude,
            longitude=longitude,
            start_date=start_date,
            end_date=end_date,
            daily=daily,
            timezone=timezone,
            # Only sent when asked for, so the API default applies otherwise
            disable_bias_correction=disable_bias_correction or None,
            cell_selection=cell_selection,
            precipitation_unit=precipitation_unit,
            temperature_unit=temperature_unit,
            wind_speed_unit=wind_speed_unit,
        )

    # pylint: disable-next=too-many-arguments,too-many-locals
    async def seasonal(  # noqa: PLR0913
        self,
        *,
        latitude: float,
        longitude: float,
        timezone: str = "UTC",
        hourly: list[HourlyParameters] | None = None,
        daily: list[DailyParameters] | None = None,
        weekly: list[SeasonalWeeklyParameters] | None = None,
        monthly: list[SeasonalMonthlyParameters] | None = None,
        forecast_days: int | None = None,
        past_days: int | None = None,
        start_date: date | None = None,
        end_date: date | None = None,
        cell_selection: CellSelection | None = None,
        models: list[str] | None = None,
        precipitation_unit: PrecipitationUnit = PrecipitationUnit.MILLIMETERS,
        temperature_unit: TemperatureUnit = TemperatureUnit.CELSIUS,
        wind_speed_unit: WindSpeedUnit = WindSpeedUnit.KILOMETERS_PER_HOUR,
    ) -> Seasonal:
        """Get the seasonal forecast, up to seven months ahead.

        Seasonal forecasts come from ensemble models of ECMWF. The hourly data
        has a resolution of 6 hours; it and the daily data have all ensemble
        members, in their members, keyed by member number. The weekly and
        monthly data are statistics over the members, like the anomaly
        compared to the model climate.

        Weekly data comes from EC46, which forecasts 46 days ahead, and
        monthly data from SEAS5, which forecasts seven months ahead. The
        default seamless model combines both; selecting one of them leaves out
        the data the other one has.

        Args:
        ----
            latitude: Latitude of the location.
            longitude: Longitude of the location.
            timezone: All timestamps are returned as local time and data is
                returned starting at 0:00 local time.
            hourly: A list of weather variables to get 6-hourly data for.
            daily: A list of daily weather variables to query for.
            weekly: A list of weekly statistics to query for.
            monthly: A list of monthly statistics to query for.
            forecast_days: Number of days to forecast (0-217). Leave unset for
                the API default of 183 days.
            past_days: Number of past days to include as well.
            start_date: First day of the time interval to return. Use it
                together with end_date, instead of forecast_days.
            end_date: Last day of the time interval to return.
            cell_selection: How to match the location to a grid cell of the
                seasonal model.
            models: Seasonal models to use, by their Open-Meteo name, like
                "ecmwf_seas5" or "ecmwf_ec46". Works the same as for the
                forecast, except that best_match can't be combined with other
                models.
            precipitation_unit: Precipitation unit.
            temperature_unit: Temperature unit.
            wind_speed_unit: Wind speed unit.

        Returns:
        -------
            A Seasonal object.

        Raises:
        ------
            ValueError: best_match is combined with other models.

        """
        # The seasonal API returns best_match data under the name of the model
        # it picked, so there is no telling it apart
        if models is not None and "best_match" in models and len(set(models)) > 1:
            msg = "best_match can't be combined with other seasonal models"
            raise ValueError(msg)

        return await self._request_with_models(
            "https://seasonal-api.open-meteo.com/v1/seasonal",
            Seasonal,
            models=models,
            latitude=latitude,
            longitude=longitude,
            timezone=timezone,
            hourly=hourly,
            daily=daily,
            weekly=weekly,
            monthly=monthly,
            forecast_days=forecast_days,
            past_days=past_days,
            start_date=start_date,
            end_date=end_date,
            cell_selection=cell_selection,
            precipitation_unit=precipitation_unit,
            temperature_unit=temperature_unit,
            wind_speed_unit=wind_speed_unit,
        )

    # pylint: disable-next=too-many-arguments
    async def flood(  # noqa: PLR0913
        self,
        *,
        latitude: float,
        longitude: float,
        daily: list[FloodParameters],
        timezone: str = "UTC",
        forecast_days: int | None = None,
        past_days: int | None = None,
        start_date: date | None = None,
        end_date: date | None = None,
        ensemble: bool = False,
        cell_selection: CellSelection | None = None,
        models: list[str] | None = None,
    ) -> Flood:
        """Get the river discharge forecast, for the river nearest to a location.

        River discharge comes from the Global Flood Awareness System (GloFAS),
        with data back to 1984. Due to its resolution of about 5 km, the
        nearest river might not be the one expected; moving the coordinates
        by about 0.1 degree can help.

        Args:
        ----
            latitude: Latitude of the location.
            longitude: Longitude of the location.
            daily: A list of river discharge variables to query for.
            timezone: All timestamps are returned as local time and data is
                returned starting at 0:00 local time.
            forecast_days: Number of days to forecast (0-366). Leave unset for
                the API default of 92 days.
            past_days: Number of past days to include as well.
            start_date: First day of the time interval to return. Use it
                together with end_date, instead of forecast_days.
            end_date: Last day of the time interval to return.
            ensemble: Return all ensemble members as well. They end up in
                daily.members, keyed by member number; the regular values
                are the control run.
            cell_selection: How to match the location to a grid cell of the
                flood model.
            models: Flood models to use, by their Open-Meteo name, like
                "seamless_v4". Works the same as for the forecast: with
                multiple models, the data of each model is in Flood.models.

        Returns:
        -------
            A Flood object.

        """
        return await self._request_with_models(
            "https://flood-api.open-meteo.com/v1/flood",
            Flood,
            models=models,
            # The flood API suffixes best_match data as flood_best_match
            model_suffixes={"best_match": "flood_best_match"},
            latitude=latitude,
            longitude=longitude,
            daily=daily,
            timezone=timezone,
            forecast_days=forecast_days,
            past_days=past_days,
            start_date=start_date,
            end_date=end_date,
            # Only sent when asked for, so the API default applies otherwise
            ensemble=ensemble or None,
            cell_selection=cell_selection,
        )

    # pylint: disable-next=too-many-arguments,too-many-locals
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
        forecast_hours: int | None = None,
        past_hours: int | None = None,
        start_date: date | None = None,
        end_date: date | None = None,
        start_hour: datetime | None = None,
        end_hour: datetime | None = None,
        temporal_resolution: TemporalResolution | None = None,
        domains: AirQualityDomain | None = None,
        cell_selection: CellSelection | None = None,
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
            forecast_hours: Number of hourly steps to return from now on,
                instead of whole days.
            past_hours: Number of past hourly steps to include, instead of
                whole days.
            start_date: First day of the time interval to return. Use it
                together with end_date, instead of forecast_days.
            end_date: Last day of the time interval to return.
            start_hour: First hour of the time interval to return. Use it
                together with end_hour. This is local time in the requested
                timezone; tzinfo is not used.
            end_hour: Last hour of the time interval to return.
            temporal_resolution: Aggregate hourly data into larger time steps.
            domains: Which air quality model to use. Leave unset to combine
                the European and global domain automatically.
            cell_selection: How to match the location to a grid cell of the
                air quality model.

        Returns:
        -------
            An AirQuality object.

        """
        query = _build_query(
            latitude=latitude,
            longitude=longitude,
            timezone=timezone,
            current=current,
            hourly=hourly,
            forecast_days=forecast_days,
            past_days=past_days,
            forecast_hours=forecast_hours,
            past_hours=past_hours,
            start_date=start_date,
            end_date=end_date,
            start_hour=start_hour,
            end_hour=end_hour,
            temporal_resolution=temporal_resolution,
            domains=domains,
            cell_selection=cell_selection,
            # The models parse timestamps in ISO 8601, so never rely on the default
            timeformat=TimeFormat.ISO_8601,
        )
        url = URL("https://air-quality-api.open-meteo.com/v1/air-quality").with_query(
            query
        )
        data = await self._request(url=url)
        return AirQuality.from_json(data)

    async def geocoding(
        self,
        *,
        name: str,
        count: int = 10,
        language: str = "en",
        country_code: str | None = None,
    ) -> Geocoding:
        """Search for locations by name or postal code.

        Args:
        ----
            name: String to search for. An empty string or only 1 character
                will return an empty result set. 2 characters will only match
                exact matching locations. 3 and more characters match the
                start of location names, so typos will not match. The search
                string can be a location name or a postal code. A qualifier
                after a comma narrows the search down to a country or region,
                like "Paris, Texas".
            count: The number of search results to return. Up to 100 results
                can be retrieved.
            language: Return translated results, if available, otherwise return
                English or the native location name. Lower-cased.
            country_code: Only return results in this country, as an ISO
                3166-1 alpha-2 code, like "NL".

        Returns:
        -------
            A Geocoding object.

        """
        # Unlike every other Open-Meteo parameter, this one is camelCase; the
        # API silently ignores country_code
        query = _build_query(
            name=name,
            count=count,
            format="json",
            language=language,
            countryCode=country_code,
        )
        url = URL("https://geocoding-api.open-meteo.com/v1/search").with_query(query)
        data = await self._request(url=url)
        return Geocoding.from_json(data)

    async def geocoding_by_id(
        self,
        *,
        location_id: int,
        language: str = "en",
    ) -> GeocodingResult:
        """Get a single location by its ID, as returned by a geocoding search.

        Args:
        ----
            location_id: The ID of the location, the geo_id of a geocoding
                result.
            language: Return translated results, if available, otherwise return
                English or the native location name. Lower-cased.

        Returns:
        -------
            A GeocodingResult object.

        Raises:
        ------
            OpenMeteoError: The location ID is unknown.

        """
        query = _build_query(id=location_id, format="json", language=language)
        url = URL("https://geocoding-api.open-meteo.com/v1/get").with_query(query)
        data = await self._request(url=url)
        return GeocodingResult.from_json(data)

    async def elevation(
        self,
        *,
        latitude: float | list[float],
        longitude: float | list[float],
    ) -> Elevation:
        """Get the elevation above sea level for one or more coordinates.

        Args:
        ----
            latitude: Latitude of the location, or a list of latitudes for
                as many as 100 locations at once.
            longitude: Longitude of the location, or a list of longitudes,
                in the same order and of the same length as the latitudes.

        Returns:
        -------
            An Elevation object containing the elevation in meters. This is
            always a list, with one value per coordinate, in the order the
            coordinates were given.

        """
        query = _build_query(latitude=latitude, longitude=longitude)
        url = URL("https://api.open-meteo.com/v1/elevation").with_query(query)
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
