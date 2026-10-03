"""Asynchronous client for the Open-Meteo API."""

# pylint: disable=protected-access

import aiohttp
import pytest
from aioresponses import aioresponses
from yarl import URL

from open_meteo import OpenMeteo
from open_meteo.exceptions import OpenMeteoError


async def test_json_request() -> None:
    """Test JSON response is handled correctly."""
    with aioresponses() as mocked:
        mocked.get(
            "http://example.com/api/",
            status=200,
            body='{"status": "ok"}',
            content_type="application/json",
        )
        async with aiohttp.ClientSession() as session:
            open_meteo = OpenMeteo(session=session)
            response = await open_meteo._request(URL("http://example.com/api/"))
            assert response == '{"status": "ok"}'


async def test_internal_session() -> None:
    """Test JSON response is handled correctly."""
    with aioresponses() as mocked:
        mocked.get(
            "http://example.com/api/",
            status=200,
            body='{"status": "ok"}',
            content_type="application/json",
        )
        async with OpenMeteo() as open_meteo:
            response = await open_meteo._request(URL("http://example.com/api/"))
            assert response == '{"status": "ok"}'


async def test_http_error400() -> None:
    """Test HTTP 404 response handling."""
    with aioresponses() as mocked:
        mocked.get(
            "http://example.com/api/",
            status=404,
            body="OMG PUPPIES!",
            content_type="text/plain",
        )
        async with aiohttp.ClientSession() as session:
            open_meteo = OpenMeteo(session=session)
            with pytest.raises(OpenMeteoError):
                await open_meteo._request(URL("http://example.com/api/"))


async def test_http_error500() -> None:
    """Test HTTP 500 response handling."""
    with aioresponses() as mocked:
        mocked.get(
            "http://example.com/api/",
            status=500,
            body='{"status":"nok"}',
            content_type="application/json",
        )
        async with aiohttp.ClientSession() as session:
            open_meteo = OpenMeteo(session=session)
            with pytest.raises(OpenMeteoError):
                await open_meteo._request(URL("http://example.com/api/"))
