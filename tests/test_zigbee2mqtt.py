"""Asynchronous client for the Open-Meteo API."""
import pytest

from open_meteo import OpenMeteo


@pytest.mark.asyncio
async def test_something():
    """Test Something."""
    open_meteo = OpenMeteo(test="test")
    assert open_meteo.test == "test"
