"""Asynchronous client for the Open-Meteo API."""
import asyncio

from open_meteo import OpenMeteo
from open_meteo.models import DailyParameters, HourlyParameters


async def main() -> None:
    """Show example on using the Open-Meteo API client."""
    async with OpenMeteo() as open_meteo:
        forecast = await open_meteo.forecast(
            latitude=52.27,
            longitude=6.87417,
            current_weather=True,
            daily=[
                DailyParameters.SUNRISE,
                DailyParameters.SUNSET,
            ],
            hourly=[
                HourlyParameters.TEMPERATURE_2M,
                HourlyParameters.RELATIVE_HUMIDITY_2M,
            ],
        )
        print(forecast)


if __name__ == "__main__":
    asyncio.run(main())
