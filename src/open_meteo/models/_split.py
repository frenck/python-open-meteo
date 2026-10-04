"""Helpers that group the suffixed variables of the API into objects."""

from __future__ import annotations

import re
from typing import Any

# The API returns ensemble members and previous model runs as one variable
# per member or run, like river_discharge_member01 or
# temperature_2m_previous_day1
ENSEMBLE_MEMBER_KEY = re.compile(r"^(?P<variable>[A-Za-z0-9_]+)_member(?P<key>\d+)$")


PREVIOUS_DAY_KEY = re.compile(r"^(?P<variable>[A-Za-z0-9_]+)_previous_day(?P<key>\d+)$")


# Ensemble mean models return the spread over the members, the standard
# deviation, as one variable per variable, like temperature_2m_spread
SPREAD_KEY = re.compile(r"^(?P<variable>[A-Za-z0-9_]+)_spread$")


def _split_suffixed(
    data: dict[Any, Any],
    pattern: re.Pattern[str],
    target: str,
) -> dict[Any, Any]:
    """Group the variables with a numbered suffix of a section, by number.

    With the ensemble member pattern and members as target,
    river_discharge_member01 ends up as the river_discharge of members[1].
    Each group gets the timestamps of the section as well, so it parses as a
    section of its own.
    """
    data = dict(data)
    groups: dict[int, dict[str, Any]] = {}
    for key in list(data):
        match = pattern.match(key)
        if match is None:
            continue

        groups.setdefault(int(match["key"]), {})[match["variable"]] = data.pop(key)

    if groups:
        for group in groups.values():
            group.update(
                {key: data[key] for key in ("time", "interval") if key in data}
            )
        data[target] = groups

    return data


def _split_members(data: dict[Any, Any]) -> dict[Any, Any]:
    """Group the ensemble members by member number, into members.

    The regular variables hold the control run, which is member 0.
    """
    return _split_suffixed(data, ENSEMBLE_MEMBER_KEY, "members")


def _split_previous_days(data: dict[Any, Any]) -> dict[Any, Any]:
    """Group the previous model runs by day, into previous_days.

    The regular variables hold the latest model run, which is day 0.
    """
    return _split_suffixed(data, PREVIOUS_DAY_KEY, "previous_days")


def _split_spread(data: dict[Any, Any]) -> dict[Any, Any]:
    """Move the spread of the variables of a section into spread.

    temperature_2m_spread ends up as the temperature_2m of spread, which
    gets the timestamps of the section as well, so it parses as a section of
    its own.
    """
    data = dict(data)
    spread = {
        match["variable"]: data.pop(key)
        for key in list(data)
        if (match := SPREAD_KEY.match(key))
    }

    if spread:
        spread.update({key: data[key] for key in ("time", "interval") if key in data})
        data["spread"] = spread

    return data


def _drop_suffixed(data: dict[Any, Any]) -> dict[Any, Any]:
    """Drop the units of members and previous runs.

    Those are the same as the unit of their variable. The spread is not: the
    spread of a temperature in °C is in K, so its units are split instead.
    """
    return {
        key: value
        for key, value in data.items()
        if not ENSEMBLE_MEMBER_KEY.match(key) and not PREVIOUS_DAY_KEY.match(key)
    }
