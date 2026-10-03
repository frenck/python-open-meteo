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
quick example that shows the current temperature in Enschede:

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
        )
        print(f"It is {forecast.current.temperature_2m} °C in Enschede")


if __name__ == "__main__":
    asyncio.run(main())
```

Open-Meteo only returns the variables you ask for, so every field on the
returned models is optional. Fields you did not request are `None`.

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

### Marine

The marine API forecasts waves, swell, ocean currents, sea surface temperature,
and sea level. It only has data at sea; on land, all values are `None`.

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
```

`results` is `None` when nothing matches.

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
from open_meteo import OpenMeteo, OpenMeteoConnectionError, OpenMeteoError

try:
    async with OpenMeteo() as open_meteo:
        await open_meteo.forecast(latitude=999, longitude=0)
except OpenMeteoConnectionError:
    # Timeouts, DNS failures, or any other connection problem
    ...
except OpenMeteoError as err:
    # The API rejected the request; the message tells you why, like:
    # "Latitude must be in range of -90 to 90°. Given: 999.0."
    print(err)
```

`OpenMeteoConnectionError` is a subclass of `OpenMeteoError`, so catching
`OpenMeteoError` alone handles both.

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
