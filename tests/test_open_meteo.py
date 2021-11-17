"""Asynchronous client for the Open-Meteo API."""
# pylint: disable=protected-access
import asyncio

import aiohttp
import pytest
from yarl import URL

from open_meteo import OpenMeteo
from open_meteo.exceptions import OpenMeteoConnectionError, OpenMeteoError


@pytest.mark.asyncio
async def test_json_request(aresponses):
    """Test JSON response is handled correctly."""
    aresponses.add(
        "example.com",
        "/api/",
        "GET",
        aresponses.Response(
            status=200,
            headers={"Content-Type": "application/json"},
            text='{"status": "ok"}',
        ),
    )
    async with aiohttp.ClientSession() as session:
        open_meteo = OpenMeteo(session=session)
        response = await open_meteo._request(URL("http://example.com/api/"))
        assert response["status"] == "ok"


@pytest.mark.asyncio
async def test_internal_session(aresponses):
    """Test JSON response is handled correctly."""
    aresponses.add(
        "example.com",
        "/api/",
        "GET",
        aresponses.Response(
            status=200,
            headers={"Content-Type": "application/json"},
            text='{"status": "ok"}',
        ),
    )
    async with OpenMeteo() as open_meteo:
        response = await open_meteo._request(URL("http://example.com/api/"))
        assert response["status"] == "ok"


@pytest.mark.asyncio
async def test_timeout(aresponses):
    """Test request timeout."""
    # Faking a timeout by sleeping
    async def response_handler(_):
        await asyncio.sleep(2)
        return aresponses.Response(body="Goodmorning!")

    aresponses.add("example.com", "/api/", "POST", response_handler)

    async with aiohttp.ClientSession() as session:
        open_meteo = OpenMeteo(
            session=session,
            request_timeout=1,
        )
        with pytest.raises(OpenMeteoConnectionError):
            assert await open_meteo._request(URL("http://example.com/api/"))


@pytest.mark.asyncio
async def test_http_error400(aresponses):
    """Test HTTP 404 response handling."""
    aresponses.add(
        "example.com",
        "/api/",
        "GET",
        aresponses.Response(text="OMG PUPPIES!", status=404),
    )

    async with aiohttp.ClientSession() as session:
        open_meteo = OpenMeteo(session=session)
        with pytest.raises(OpenMeteoError):
            assert await open_meteo._request(URL("http://example.com/api/"))


@pytest.mark.asyncio
async def test_http_error500(aresponses):
    """Test HTTP 500 response handling."""
    aresponses.add(
        "example.com",
        "/api/",
        "GET",
        aresponses.Response(
            body=b'{"status":"nok"}',
            status=500,
            headers={"Content-Type": "application/json"},
        ),
    )

    async with aiohttp.ClientSession() as session:
        open_meteo = OpenMeteo(session=session)
        with pytest.raises(OpenMeteoError):
            assert await open_meteo._request(URL("http://example.com/api/"))
