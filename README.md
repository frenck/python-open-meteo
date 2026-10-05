# Python: Asynchronous client for the Open-Meteo API

[![GitHub Release][releases-shield]][releases]
[![Python Versions][python-versions-shield]][pypi]
![Project Stage][project-stage-shield]
![Project Maintenance][maintenance-shield]
[![License][license-shield]](LICENSE.md)

[![Build Status][build-shield]][build]
[![Code Coverage][codecov-shield]][codecov]
[![OpenSSF Scorecard][scorecard-shield]][scorecard]
[![Open in Dev Containers][devcontainer-shield]][devcontainer]

[![Sponsor Frenck via GitHub Sponsors][github-sponsors-shield]][github-sponsors]

[![Support Frenck on Patreon][patreon-shield]][patreon]

Asynchronous Python client for the Open-Meteo API.

## About

[Open-Meteo][open-meteo] offers free weather forecast APIs for open-source
developers and non-commercial use. No API key is required.

This package is an asynchronous Python client for it, covering the weather
forecast, air quality, geocoding, and elevation APIs. It is mainly created to
allow third-party programs to use Open-Meteo data. Home Assistant, for
example, uses it for its Open-Meteo integration.

## Installation

```bash
pip install open-meteo
```

## Usage

The client is an async context manager; every API call is a coroutine. A
quick example that gets the current and hourly temperature in Enschede:

```python
import asyncio

from open_meteo import HourlyParameters, OpenMeteo


async def main() -> None:
    """Show example of using the Open-Meteo API client."""
    async with OpenMeteo() as open_meteo:
        forecast = await open_meteo.forecast(
            latitude=52.27,
            longitude=6.87417,
            current=[HourlyParameters.TEMPERATURE_2M],
            hourly=[HourlyParameters.TEMPERATURE_2M],
        )
        print(f"It is {forecast.current.temperature_2m} °C in Enschede")


if __name__ == "__main__":
    asyncio.run(main())
```

Open-Meteo only returns the variables you ask for, so the variables and
sections on the returned models are optional: those you did not request are
`None`. A requested series can contain `None` values as well, where a weather
model has no data, like at the end of a long forecast. Those keep their place,
so the values stay aligned with their timestamps:

```python
for time, temperature in zip(
    forecast.hourly.time, forecast.hourly.temperature_2m, strict=True
):
    if temperature is not None:
        print(time, temperature)
```

Timestamps are local time in the requested `timezone`, UTC by default, as
naive datetimes. The offset to UTC is on the response, to make them aware
when you need to compare them with other times:

```python
from datetime import timedelta, timezone

offset = timezone(timedelta(seconds=forecast.utc_offset_seconds))
observed_at = forecast.current.time.replace(tzinfo=offset)
```

### Weather forecast

Request current conditions, hourly data, and daily data in a single call.
Every hourly variable is also available as a current condition.

```python
from open_meteo import (
    DailyParameters,
    HourlyParameters,
    OpenMeteo,
    TemperatureUnit,
    WindSpeedUnit,
)

async with OpenMeteo() as open_meteo:
    forecast = await open_meteo.forecast(
        latitude=52.27,
        longitude=6.87417,
        timezone="Europe/Amsterdam",
        current=[
            HourlyParameters.TEMPERATURE_2M,
            HourlyParameters.WEATHER_CODE,
            HourlyParameters.IS_DAY,
        ],
        hourly=[
            HourlyParameters.TEMPERATURE_2M,
            HourlyParameters.PRECIPITATION_PROBABILITY,
        ],
        daily=[
            DailyParameters.TEMPERATURE_2M_MAX,
            DailyParameters.SUNRISE,
            DailyParameters.SUNSET,
        ],
        forecast_days=3,
        temperature_unit=TemperatureUnit.FAHRENHEIT,
        wind_speed_unit=WindSpeedUnit.METERS_PER_SECOND,
    )

    # Current conditions, with their units
    current = forecast.current
    print(current.temperature_2m, forecast.current_units.temperature_2m)

    # Hourly and daily data are lists, aligned with their time list
    for time, temperature in zip(
        forecast.hourly.time, forecast.hourly.temperature_2m, strict=True
    ):
        print(time, temperature)

    for day, sunrise in zip(forecast.daily.time, forecast.daily.sunrise, strict=True):
        print(day, sunrise)
```

Leave out `forecast_days` to get the API default of 7 days (up to 16), and
use `past_days` to include data from the past as well.

By default, the API picks the best weather models for the location. Pick them
yourself with `models`. With a single model, the data stays where it is. With
multiple models, the data of each model ends up in a forecast of its own, in
`forecast.models`, while the current conditions stay on the forecast itself:

```python
from open_meteo import HourlyParameters, OpenMeteo

async with OpenMeteo() as open_meteo:
    forecast = await open_meteo.forecast(
        latitude=52.27,
        longitude=6.87417,
        hourly=[HourlyParameters.TEMPERATURE_2M],
        models=["icon_seamless", "gfs_seamless"],
    )

    for name, model in forecast.models.items():
        print(name, model.hourly.temperature_2m)
```

When only one of the models has data for the location, the API returns its
data without telling which model it is from. It then stays on the forecast
itself, like with a single model, and `forecast.models` is `None`.

Weather higher up in the atmosphere is available on pressure levels, like 850
or 500 hPa. Those end up per level, for the hourly data by default, or for the
current conditions and 15-minutely data with `pressure_level_sections`.

```python
from open_meteo import ForecastSection, OpenMeteo, PressureLevelVariable

async with OpenMeteo() as open_meteo:
    forecast = await open_meteo.forecast(
        latitude=52.27,
        longitude=6.87417,
        pressure_level_variables=[PressureLevelVariable.TEMPERATURE],
        pressure_levels=[850, 500],
        pressure_level_sections=[ForecastSection.CURRENT, ForecastSection.HOURLY],
    )

    print(forecast.current.pressure_levels[850].temperature)
    print(forecast.hourly.pressure_levels[500].temperature)
```

Some models, like UKMO, DMI, and KNMI, also have data at heights above ground,
like 300 or 1000 meters. Those work the same, with `height_level_variables`,
`height_levels`, and `height_level_sections`, and end up per height in meters.
Heights that are a variable of their own, like `temperature_80m`, stay there.

```python
from open_meteo import HeightLevelVariable, OpenMeteo

async with OpenMeteo() as open_meteo:
    forecast = await open_meteo.forecast(
        latitude=51.5,
        longitude=-0.12,
        models=["ukmo_seamless"],
        height_level_variables=[HeightLevelVariable.WIND_SPEED],
        height_levels=[300, 1000],
    )

    print(forecast.hourly.height_levels[1000].wind_speed)
```

### Ensemble forecast

Ensemble models run the same forecast many times, with slightly different
starting conditions, to show how certain a forecast is. The regular values are
the control run, and every other run is a member.

```python
from open_meteo import HourlyParameters, OpenMeteo

async with OpenMeteo() as open_meteo:
    forecast = await open_meteo.ensemble(
        latitude=52.27,
        longitude=6.87417,
        models=["ecmwf_ifs025_ensemble"],
        hourly=[HourlyParameters.TEMPERATURE_2M],
    )

    print(forecast.hourly.temperature_2m)
    for number, member in forecast.hourly.members.items():
        print(number, member.temperature_2m)
```

The ensemble mean models, like `ecmwf_ifs025_ensemble_mean`, return the mean
over all members. With `spread=True`, they return the spread as well, the
standard deviation, in `forecast.hourly.spread`.

### Seasonal forecast

The seasonal API forecasts up to seven months ahead. Besides 6-hourly and daily
data with all ensemble members, it has weekly and monthly statistics, like how
much warmer or colder than normal it will likely be.

```python
from open_meteo import OpenMeteo, SeasonalMonthlyParameters, SeasonalWeeklyParameters

async with OpenMeteo() as open_meteo:
    seasonal = await open_meteo.seasonal(
        latitude=52.27,
        longitude=6.87417,
        weekly=[SeasonalWeeklyParameters.TEMPERATURE_2M_ANOMALY],
        monthly=[SeasonalMonthlyParameters.PRECIPITATION_ANOMALY],
    )

    print(seasonal.weekly.time, seasonal.weekly.temperature_2m_anomaly)
    print(seasonal.monthly.time, seasonal.monthly.precipitation_anomaly)
```

### Previous model runs

The previous runs API shows what the weather models forecasted for each hour,
one to seven days before it. `previous_days[1]` holds, for every hour, the
forecast made about a day earlier, so one series combines several model runs.
That shows how a forecast changed, or how accurate forecasts were. For one
complete run of a model, use the single runs API instead.

```python
from open_meteo import HourlyParameters, OpenMeteo

async with OpenMeteo() as open_meteo:
    forecast = await open_meteo.previous_runs(
        latitude=52.27,
        longitude=6.87417,
        previous_days=[1, 2],
        hourly=[HourlyParameters.TEMPERATURE_2M],
    )

    print(forecast.hourly.temperature_2m)
    print(forecast.hourly.previous_days[1].temperature_2m)
```

### Single model runs

The single runs API returns the forecast of one specific run of a weather
model, starting at the time it ran. The run is in UTC.

```python
from datetime import UTC, datetime

from open_meteo import HourlyParameters, OpenMeteo

async with OpenMeteo() as open_meteo:
    forecast = await open_meteo.single_run(
        latitude=52.27,
        longitude=6.87417,
        run=datetime(2026, 9, 1, 0, 0, tzinfo=UTC),
        hourly=[HourlyParameters.TEMPERATURE_2M],
        models=["ecmwf_ifs"],
    )

    print(forecast.hourly.time[0], forecast.hourly.temperature_2m)
```

### Satellite radiation

The satellite radiation API has the solar radiation measured by weather
satellites, back to 1983, every 10 to 30 minutes. There is no data for North
America yet; for a location without data, it raises an `OpenMeteoError`.

```python
from open_meteo import HourlyParameters, OpenMeteo, TemporalResolution

async with OpenMeteo() as open_meteo:
    satellite = await open_meteo.satellite_radiation(
        latitude=52.27,
        longitude=6.87417,
        past_days=1,
        hourly=[HourlyParameters.SHORTWAVE_RADIATION],
        temporal_resolution=TemporalResolution.NATIVE,
    )

    print(satellite.hourly.time, satellite.hourly.shortwave_radiation)
```

### Historical forecast

The historical forecast API archives the forecasts the weather models made in
the past, back to 2016. It takes the same variables and models as the forecast,
for a range of dates.

```python
from datetime import date

from open_meteo import DailyParameters, OpenMeteo

async with OpenMeteo() as open_meteo:
    forecast = await open_meteo.historical_forecast(
        latitude=52.27,
        longitude=6.87417,
        start_date=date(2024, 1, 1),
        end_date=date(2024, 1, 7),
        daily=[DailyParameters.TEMPERATURE_2M_MAX],
    )

    print(forecast.daily.temperature_2m_max)
```

### Historical weather

The historical weather API has the weather of the past, back to 1940, from
reanalysis datasets like ERA5. Those combine weather observations and weather
models into the best estimate of what the weather was.

```python
from datetime import date

from open_meteo import DailyParameters, OpenMeteo

async with OpenMeteo() as open_meteo:
    weather = await open_meteo.historical_weather(
        latitude=52.27,
        longitude=6.87417,
        start_date=date(1953, 1, 31),
        end_date=date(1953, 2, 1),
        daily=[DailyParameters.WIND_GUSTS_10M_MAX],
    )

    print(weather.daily.wind_gusts_10m_max)
```

### Climate projections

The climate API has climate projections from 1950 up to 2050, from high
resolution climate models. These are meant for long term trends, like the
change in temperature over decades, not for the weather of a specific day.

```python
from datetime import date

from open_meteo import DailyParameters, OpenMeteo

async with OpenMeteo() as open_meteo:
    climate = await open_meteo.climate(
        latitude=52.27,
        longitude=6.87417,
        start_date=date(2050, 7, 1),
        end_date=date(2050, 7, 31),
        daily=[DailyParameters.TEMPERATURE_2M_MAX],
        models=["MRI_AGCM3_2_S"],
    )

    print(climate.daily.temperature_2m_max)
```

### Marine

The marine API forecasts waves, swell, ocean currents, sea surface temperature,
and sea level. It only has data at sea: by default, the nearest sea grid cell
is used, so locations near the coast get data too. Further inland, all values
are `None`.

```python
from open_meteo import MarineDailyParameters, MarineParameters, OpenMeteo

async with OpenMeteo() as open_meteo:
    marine = await open_meteo.marine(
        latitude=53.0,
        longitude=4.0,
        current=[
            MarineParameters.WAVE_HEIGHT,
            MarineParameters.SEA_SURFACE_TEMPERATURE,
        ],
        daily=[MarineDailyParameters.WAVE_HEIGHT_MAX],
    )

    print(marine.current.wave_height, marine.current.sea_surface_temperature)
    print(marine.daily.wave_height_max)
```

### River discharge

The flood API forecasts the daily river discharge of the river nearest to a
location, from the Global Flood Awareness System (GloFAS). With `ensemble`,
it returns all ensemble members as well.

```python
from open_meteo import FloodParameters, OpenMeteo

async with OpenMeteo() as open_meteo:
    flood = await open_meteo.flood(
        latitude=51.84,
        longitude=6.11,
        daily=[
            FloodParameters.RIVER_DISCHARGE,
            FloodParameters.RIVER_DISCHARGE_MAX,
        ],
        ensemble=True,
    )

    print(flood.daily.river_discharge)
    print(flood.daily.members[1].river_discharge)
```

### Air quality

Air quality works the same way, with its own set of variables. These include
particulate matter, gases, pollen (Europe only), and both the European and US
air quality indices.

```python
from open_meteo import AirQualityParameters, OpenMeteo

async with OpenMeteo() as open_meteo:
    air_quality = await open_meteo.air_quality(
        latitude=52.27,
        longitude=6.87417,
        current=[
            AirQualityParameters.EUROPEAN_AQI,
            AirQualityParameters.PM2_5,
        ],
        hourly=[AirQualityParameters.BIRCH_POLLEN],
    )

    print(air_quality.current.european_aqi)
    print(air_quality.hourly.birch_pollen)
```

### Geocoding

Search for a location by name or postal code. This is handy to find the
coordinates and timezone to use with the other APIs.

```python
from open_meteo import OpenMeteo

async with OpenMeteo() as open_meteo:
    geocoding = await open_meteo.geocoding(name="Enschede", count=3)

    for result in geocoding.results or []:
        print(result.name, result.country, result.latitude, result.longitude)

    # A result can be looked up again later, by its ID
    if geocoding.results:
        location = await open_meteo.geocoding_by_id(
            location_id=geocoding.results[0].geo_id,
        )
        print(location.name, location.timezone)
```

`results` is `None` when nothing matches. `geocoding_by_id` returns that
single result.

### Elevation

Look up the elevation of a location, in meters above sea level.

```python
from open_meteo import OpenMeteo

async with OpenMeteo() as open_meteo:
    elevation = await open_meteo.elevation(latitude=52.27, longitude=6.87417)

    print(elevation.elevation[0])
```

### Connection options

All constructor arguments are optional:

```python
OpenMeteo(
    request_timeout=10,  # per-request timeout in seconds (default: 10)
)
```

You may also pass your own `aiohttp.ClientSession` via `session=...` to
share a connection pool. The client leaves a session you pass in open, and
only closes the one it created itself.

### Error handling

```python
from open_meteo import (
    OpenMeteo,
    OpenMeteoConnectionError,
    OpenMeteoError,
    OpenMeteoRateLimitError,
    OpenMeteoResponseError,
)

try:
    async with OpenMeteo() as open_meteo:
        await open_meteo.forecast(latitude=999, longitude=0)
except OpenMeteoConnectionError:
    # Timeouts, DNS failures, or any other connection problem
    ...
except OpenMeteoRateLimitError as err:
    # Too many requests; retry_after has the seconds to wait, if the API
    # said so
    print(err.retry_after)
except OpenMeteoResponseError as err:
    # The API rejected the request; reason tells you why, like:
    # "Latitude must be in range of -90 to 90°. Given: 999.0."
    print(err.status, err.reason)
except OpenMeteoError:
    # Anything else unexpected, like a response that couldn't be parsed
    ...
```

Every exception for a failed request or an unexpected response is a subclass
of `OpenMeteoError`, so catching that alone handles all of them. Invalid
combinations of arguments raise a `ValueError` before anything is requested,
like only one of `pressure_level_variables` and `pressure_levels`. The request
timeout covers the whole request, including reading the response.

## Changelog & Releases

This repository keeps a change log using [GitHub's releases][releases]
functionality. The format of the log is based on
[Keep a Changelog][keepchangelog].

Releases are based on [Semantic Versioning][semver], and use the format
of `MAJOR.MINOR.PATCH`. In a nutshell, the version will be incremented
based on the following:

- `MAJOR`: Incompatible or major changes.
- `MINOR`: Backwards-compatible new features and enhancements.
- `PATCH`: Backwards-compatible bugfixes and package updates.

## Contributing

This is an active open-source project. We are always open to people who want to
use the code or contribute to it.

We've set up a separate document for our
[contribution guidelines](.github/CONTRIBUTING.md).

Thank you for being involved! :heart_eyes:

## Setting up development environment

This Python project is fully managed using the [Poetry][poetry] dependency
manager. But also relies on the use of NodeJS for certain checks during
development.

You need at least:

- Python 3.11+
- [Poetry][poetry-install]
- NodeJS 24+ (including NPM)

To install all packages, including all development requirements:

```bash
npm install
poetry install
poetry run prek install
```

As this repository uses the [prek][prek] framework, all changes
are linted and tested with each commit. You can run all checks and tests
manually, using the following command:

```bash
poetry run prek run --all-files
```

To run just the Python tests:

```bash
poetry run pytest
```

## Authors & contributors

The original setup of this repository is by [Franck Nijhof][frenck].

For a full list of all authors and contributors,
check [the contributor's page][contributors].

## Disclaimer

This project is an independent, community-driven effort. It is **not
affiliated with, endorsed by, or supported by** Open-Meteo.

The free Open-Meteo API is for non-commercial use only, and its data is
licensed under [Attribution 4.0 International (CC BY 4.0)][cc-by]. If you
use this library, those terms apply to you as well. Read the
[Open-Meteo terms][open-meteo-terms] for the details, including the rate
limits and the attribution requirements.

This library talks to the free API only. The commercial API, which needs an
API key, is not supported.

## License

MIT License

Copyright (c) 2021-2026 Franck Nijhof

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

[build-shield]: https://github.com/frenck/python-open-meteo/actions/workflows/tests.yaml/badge.svg
[build]: https://github.com/frenck/python-open-meteo/actions/workflows/tests.yaml
[cc-by]: https://creativecommons.org/licenses/by/4.0/
[codecov-shield]: https://codecov.io/gh/frenck/python-open-meteo/branch/main/graph/badge.svg
[codecov]: https://codecov.io/gh/frenck/python-open-meteo
[contributors]: https://github.com/frenck/python-open-meteo/graphs/contributors
[devcontainer-shield]: https://img.shields.io/static/v1?label=Dev%20Containers&message=Open&color=blue&logo=visualstudiocode
[devcontainer]: https://vscode.dev/redirect?url=vscode://ms-vscode-remote.remote-containers/cloneInVolume?url=https://github.com/frenck/python-open-meteo
[frenck]: https://github.com/frenck
[github-sponsors-shield]: https://frenck.dev/wp-content/uploads/2019/12/github_sponsor.png
[github-sponsors]: https://github.com/sponsors/frenck
[keepchangelog]: http://keepachangelog.com/en/1.0.0/
[license-shield]: https://img.shields.io/github/license/frenck/python-open-meteo.svg
[maintenance-shield]: https://img.shields.io/maintenance/yes/2026.svg
[open-meteo-terms]: https://open-meteo.com/en/terms
[open-meteo]: https://open-meteo.com
[patreon-shield]: https://frenck.dev/wp-content/uploads/2019/12/patreon.png
[patreon]: https://www.patreon.com/frenck
[poetry-install]: https://python-poetry.org/docs/#installation
[poetry]: https://python-poetry.org
[prek]: https://github.com/j178/prek
[project-stage-shield]: https://img.shields.io/badge/project%20stage-production%20ready-brightgreen.svg
[pypi]: https://pypi.org/project/open-meteo/
[python-versions-shield]: https://img.shields.io/pypi/pyversions/open-meteo
[releases-shield]: https://img.shields.io/github/release/frenck/python-open-meteo.svg
[releases]: https://github.com/frenck/python-open-meteo/releases
[scorecard-shield]: https://api.scorecard.dev/projects/github.com/frenck/python-open-meteo/badge
[scorecard]: https://scorecard.dev/viewer/?uri=github.com/frenck/python-open-meteo
[semver]: http://semver.org/spec/v2.0.0.html
