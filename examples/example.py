"""Asynchronous client for the Open-Meteo API."""
import asyncio

from open_meteo import OpenMeteo


async def main():
    """Show example on using the Open-Meteo API client."""
    open_meteo = OpenMeteo(
        test="test",
    )
    print(open_meteo.test)


if __name__ == "__main__":
    asyncio.run(main())
