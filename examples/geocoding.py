"""Asynchronous client for the Open-Meteo API."""
import asyncio

from open_meteo import OpenMeteo


async def main():
    """Show example on using the Open-Meteo API client."""
    async with OpenMeteo() as open_meteo:
        search = await open_meteo.geocoding(
            name="Enschede",
        )
        print(search)


if __name__ == "__main__":
    asyncio.run(main())
