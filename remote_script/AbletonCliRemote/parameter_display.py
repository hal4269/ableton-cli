"""Find the raw value of a device parameter from a display value such as "800 Hz".

Raw parameter values are often non-linear (frequencies, times), so a continuous target is
found by bisection on ``parameter.str_for_value`` — Live's own display formatting, which is
computed without writing the parameter. Quantized parameters match an item of
``value_items`` by name instead.
"""

from __future__ import annotations

import math
import re
from typing import Any

#: Units normalised before comparing: frequencies to Hz, times to ms.
_UNIT_SCALE = {"khz": 1000.0, "hz": 1.0, "s": 1000.0, "ms": 1.0}
#: Units that compare as one: a target in kHz may meet a display in Hz.
_UNIT_FAMILY = {"khz": "hz", "s": "ms"}
_NUMBER = re.compile(r"([+-]?(?:\d+(?:\.\d+)?|\.\d+))\s*([a-z%]*)")
_MAX_STEPS = 60
_RELATIVE_TOLERANCE = 0.005


class ParameterDisplayError(ValueError):
    """The display value cannot be reached on this parameter."""


def display_number(display: str) -> float | None:
    """A display string as a comparable number (Hz and ms normalised); None if not numeric."""
    text = display.strip().lower()
    if text.startswith("-inf"):
        return -math.inf
    if text.startswith(("inf", "+inf")):
        return math.inf
    match = _NUMBER.match(text)
    if match is None:
        return None
    return float(match.group(1)) * _UNIT_SCALE.get(match.group(2), 1.0)


def _raw_unit(display: str) -> str:
    match = _NUMBER.match(display.strip().lower())
    return match.group(2) if match else ""


def _unit(display: str) -> str:
    unit = _raw_unit(display)
    return _UNIT_FAMILY.get(unit, unit)


def value_for_display(parameter: Any, display: str) -> float:
    if bool(getattr(parameter, "is_quantized", False)):
        return _quantized_value(parameter, display)
    want = display_number(display)
    if want is None:
        raise ParameterDisplayError(f"{display!r} is not a number with an optional unit")
    low = float(parameter.min)
    high = float(parameter.max)
    wanted_unit = _unit(display)
    shown = str(parameter.str_for_value(high))
    if wanted_unit and wanted_unit != _unit(shown):
        raise ParameterDisplayError(
            f"{parameter.name!r} is not shown in {_raw_unit(display)!r} "
            f"(Live shows {shown!r}); use {_raw_unit(shown) or 'no unit'!r}"
        )
    if want == -math.inf:
        return low
    at_low = _rendered(parameter, low)
    at_high = _rendered(parameter, high)
    if not min(at_low, at_high) <= want <= max(at_low, at_high):
        raise ParameterDisplayError(
            f"{display!r} is outside the range of {parameter.name!r} "
            f"({parameter.str_for_value(low)} .. {parameter.str_for_value(high)})"
        )
    rising = at_high >= at_low
    best = low if abs(at_low - want) <= abs(at_high - want) else high
    tolerance = max(abs(want) * _RELATIVE_TOLERANCE, 1e-6)
    for _ in range(_MAX_STEPS):
        middle = (low + high) / 2
        got = _rendered(parameter, middle)
        if abs(got - want) < abs(_rendered(parameter, best) - want):
            best = middle
        if abs(got - want) <= tolerance:
            return middle
        if (got < want) == rising:
            low = middle
        else:
            high = middle
    return best


def _rendered(parameter: Any, value: float) -> float:
    number = display_number(str(parameter.str_for_value(value)))
    if number is None:
        raise ParameterDisplayError(
            f"{parameter.name!r} displays {parameter.str_for_value(value)!r}, which is not "
            "numeric; set it with a raw value"
        )
    return number


def _quantized_value(parameter: Any, display: str) -> float:
    items = [str(item) for item in getattr(parameter, "value_items", ())]
    wanted = display.strip().lower()
    for index, item in enumerate(items):
        if item.lower() == wanted:
            return float(parameter.min) + index
    raise ParameterDisplayError(
        f"{display!r} is not an item of {parameter.name!r}: {', '.join(items)}"
    )
