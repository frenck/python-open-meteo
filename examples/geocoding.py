"""Asynchronous client for the Open-Meteo API."""

import asyncio

from open_meteo import OpenMeteo


async def main() -> None:
    """Show example on using the Open-Meteo API client."""
    async with OpenMeteo() as open_meteo:
        search = await open_meteo.geocoding(
            name="Enschede",
        )
        print(search)

        # A result can be looked up again later, by its ID
        if search.results:
            location = await open_meteo.geocoding_by_id(
                location_id=search.results[0].geo_id,
            )
            print(location)


if __name__ == "__main__":
    asyncio.run(main())
