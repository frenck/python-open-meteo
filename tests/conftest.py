"""Common fixtures and helpers for Open-Meteo tests."""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
from typing import TYPE_CHECKING, Any

import aiohttp
import pytest
from aioresponses import aioresponses
from aioresponses import core as aioresponses_core

from open_meteo import OpenMeteo

if TYPE_CHECKING:
    from collections.abc import AsyncGenerator, Generator

FIXTURES_DIR = Path(__file__).parent / "fixtures"

AIOHTTP_REQUIRES_STREAM_WRITER = (
    "stream_writer" in aiohttp.ClientResponse.__init__.__code__.co_varnames
)


AIOHTTP_STREAM_WRITER = SimpleNamespace(output_size=0)


class AioresponsesClientResponse(aioresponses_core.ClientResponse):
    """Backwards-compatible ClientResponse for aioresponses."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """Initialize and provide a stream_writer for aiohttp 3.14+."""
        kwargs.setdefault("stream_writer", AIOHTTP_STREAM_WRITER)
        super().__init__(*args, **kwargs)


@pytest.fixture(scope="session", autouse=True)
def setup_aioresponses_aiohttp_compat() -> Generator[None, None, None]:
    """Patch aioresponses ClientResponse for aiohttp compatibility in tests."""
    if not AIOHTTP_REQUIRES_STREAM_WRITER:
        yield
        return

    monkeypatch = pytest.MonkeyPatch()
    monkeypatch.setattr(aioresponses_core, "ClientResponse", AioresponsesClientResponse)
    yield
    monkeypatch.undo()


def load_fixture(name: str) -> str:
    """Load a fixture file by name."""
    return (FIXTURES_DIR / name).read_text(encoding="utf-8")


@pytest.fixture
def responses() -> Generator[aioresponses, None, None]:
    """Yield an aioresponses instance that patches aiohttp client sessions."""
    with aioresponses() as mocker:
        yield mocker


@pytest.fixture
async def open_meteo_client() -> AsyncGenerator[OpenMeteo, None]:
    """Yield an Open-Meteo client with its own session."""
    async with aiohttp.ClientSession() as session:
        yield OpenMeteo(session=session)
