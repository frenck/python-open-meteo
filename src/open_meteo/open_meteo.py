"""Asynchronous client for the Open-Meteo API."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class OpenMeteo:
    """Main class for the Open-Meteo API."""

    test: str
