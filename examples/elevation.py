"""Asynchronous client for the Open-Meteo API."""

import asyncio

from open_meteo import OpenMeteo


async def main() -> None:
    """Show example on using the Open-Meteo API client."""
    async with OpenMeteo() as open_meteo:
        result = await open_meteo.elevation(
            latitude=52.52,
            longitude=13.41,
        )
        print(result)


if __name__ == "__main__":
    asyncio.run(main())
