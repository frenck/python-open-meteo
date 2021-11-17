"""Asynchronous client for the Open-Meteo API."""
from __future__ import annotations

from enum import Enum, auto
from typing import Any


class StrEnum(str, Enum):
    """An Enum of strings.

    A backported StrEnum implementation of Python 3.11, providing roughly the
    same implementation for our use case. The `auto()` behavior uses the
    lowercase version of its member name for its value.

        Example:
        class Example(StrEnum):
            UPPER_CASE = auto()
            NOT_AUTO = "beep"

            # We should not use these, but they work
            lower_case = auto()
            MixedCase = auto()

        assert Example.UPPER_CASE == "upper_case"
        assert Example.NOT_AUTO == "beep"

        assert Example.lower_case == "lower_case"
        assert Example.MixedCase == "MixedCase"
    """

    def __new__(cls, value: str, *args: Any, **kwargs: Any) -> StrEnum:
        """Validate StrEnum creation.

        Args:
            value: Value of the member.
            args: Additional arguments.
            kwargs: Additional keyword arguments.

        Returns:
            The StrEnum instance.

        Raises:
            TypeError: If the value is not a string.
        """
        if not isinstance(value, (str, auto)):
            raise TypeError(
                f"Values of StrEnums must be strings: {value!r} is a {type(value)}"
            )
        return super().__new__(cls, value, *args, **kwargs)  # type: ignore

    def __str__(self) -> str:
        """Represent as a string.

        Returns:
            Value of the member as a string.
        """
        return str(self.value)

    @staticmethod
    def _generate_next_value_(  # pylint: disable=arguments-differ
        name: str, _start: Any, _count: Any, _last_values: Any
    ) -> str:
        """Generate the next value when not given.

        Args:
            name: the name of the member
            _start: the initial start value or None
            _count: the number of existing members
            _last_values: the last value assigned or None

        Returns:
            The next value for the member.
        """
        return name.lower()
