from __future__ import annotations

import math
from collections.abc import Callable
from dataclasses import dataclass, field

import pytest

from remote_script.AbletonCliRemote.parameter_display import (
    ParameterDisplayError,
    display_number,
    value_for_display,
)


@dataclass(slots=True)
class _Param:
    name: str
    render: Callable[[float], str]
    min: float = 0.0
    max: float = 1.0
    is_quantized: bool = False
    value_items: tuple[str, ...] = ()
    value: float = 0.0
    renders: list[float] = field(default_factory=list)

    def str_for_value(self, value: float) -> str:
        self.renders.append(value)
        return self.render(value)


def _frequency(value: float) -> str:
    hz = 20.0 * 1000.0**value
    return f"{hz / 1000:.2f} kHz" if hz >= 1000 else f"{hz:.1f} Hz"


def _filter_freq() -> _Param:
    return _Param("Filter Freq", _frequency)


def test_display_number_normalises_units() -> None:
    assert display_number("800 Hz") == 800.0
    assert display_number("1.20 kHz") == 1200.0
    assert display_number("120 ms") == 120.0
    assert display_number("1.5 s") == 1500.0
    assert display_number("-6.0 dB") == -6.0
    assert display_number("-inf dB") == -math.inf
    assert display_number("35 %") == 35.0
    assert display_number("Saw") is None


def test_value_for_display_bisects_a_non_linear_range() -> None:
    parameter = _filter_freq()

    value = value_for_display(parameter, "800 Hz")

    assert display_number(_frequency(value)) == pytest.approx(800.0, rel=0.01)


def test_value_for_display_accepts_other_unit_than_the_display() -> None:
    parameter = _filter_freq()

    assert display_number(_frequency(value_for_display(parameter, "2 kHz"))) == pytest.approx(
        2000.0, rel=0.01
    )
    assert display_number(_frequency(value_for_display(parameter, "500hz"))) == pytest.approx(
        500.0, rel=0.01
    )


def test_value_for_display_never_writes_the_parameter() -> None:
    parameter = _filter_freq()

    value_for_display(parameter, "800 Hz")

    assert parameter.value == 0.0
    assert parameter.renders


def test_value_for_display_handles_a_falling_display() -> None:
    parameter = _Param("Inverted", lambda v: f"{(1.0 - v) * 100:.1f} %")

    value = value_for_display(parameter, "25 %")

    assert value == pytest.approx(0.75, abs=0.01)


def test_value_for_display_maps_minus_infinity_to_the_minimum() -> None:
    parameter = _Param(
        "Volume",
        lambda v: "-inf dB" if v <= 0 else f"{20 * math.log10(v):.1f} dB",
    )

    assert value_for_display(parameter, "-inf dB") == 0.0


def test_value_for_display_matches_quantized_items_case_insensitively() -> None:
    parameter = _Param(
        "Osc-A Wave",
        lambda v: ("Sine", "Saw 8", "Square")[int(v)],
        min=0.0,
        max=2.0,
        is_quantized=True,
        value_items=("Sine", "Saw 8", "Square"),
    )

    assert value_for_display(parameter, "saw 8") == 1.0


def test_value_for_display_offsets_quantized_items_by_the_minimum() -> None:
    parameter = _Param(
        "Octave",
        lambda v: str(int(v)),
        min=-2.0,
        max=0.0,
        is_quantized=True,
        value_items=("-2", "-1", "0"),
    )

    assert value_for_display(parameter, "-1") == -1.0


def test_value_for_display_rejects_unknown_quantized_item() -> None:
    parameter = _Param(
        "Mode",
        lambda v: ("A", "B")[int(v)],
        max=1.0,
        is_quantized=True,
        value_items=("A", "B"),
    )

    with pytest.raises(ParameterDisplayError, match="'C'.*A, B"):
        value_for_display(parameter, "C")


def test_value_for_display_rejects_targets_outside_the_range() -> None:
    parameter = _filter_freq()

    with pytest.raises(ParameterDisplayError, match="outside"):
        value_for_display(parameter, "30 kHz")


def test_value_for_display_rejects_non_numeric_targets() -> None:
    with pytest.raises(ParameterDisplayError, match="not a number"):
        value_for_display(_filter_freq(), "bright")


def test_value_for_display_rejects_parameters_without_numeric_display() -> None:
    parameter = _Param("Note", lambda v: "C3")

    with pytest.raises(ParameterDisplayError, match="not numeric"):
        value_for_display(parameter, "60")


def test_value_for_display_rejects_a_unit_the_parameter_does_not_display() -> None:
    parameter = _Param("Drive", lambda v: f"{v * 100:.1f} %")

    with pytest.raises(ParameterDisplayError, match="'db'.*'%'"):
        value_for_display(parameter, "6 dB")


def test_value_for_display_accepts_a_bare_number_in_the_displayed_unit() -> None:
    parameter = _Param("Drive", lambda v: f"{v * 100:.1f} %")

    assert value_for_display(parameter, "35") == pytest.approx(0.35, abs=0.01)
