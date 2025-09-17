"""Asynchronous client for the Open-Meteo Air Quality API."""

import asyncio

from open_meteo import OpenMeteo
from open_meteo.models import AirQualityParameters


async def main() -> None:
    """Show example on using the Open-Meteo Air Quality API client."""
    async with OpenMeteo() as open_meteo:
        air_quality = await open_meteo.air_quality(
            latitude=52.27,
            longitude=6.87417,
            current=[
                AirQualityParameters.PM10,
                AirQualityParameters.PM2_5,
            ],
            hourly=[
                AirQualityParameters.ALDER_POLLEN,
                AirQualityParameters.BIRCH_POLLEN,
                AirQualityParameters.GRASS_POLLEN,
                AirQualityParameters.MUGWORT_POLLEN,
                AirQualityParameters.OLIVE_POLLEN,
                AirQualityParameters.RAGWEED_POLLEN,

            ],
        )
        print(air_quality)


if __name__ == "__main__":
    asyncio.run(main())
