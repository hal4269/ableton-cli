"""Return-track devices: name, list, insert, parameter list and set by display value."""

from __future__ import annotations

from typing import Any

import pytest
from test_live_backend import _Device, _Parameter, _SurfaceStub
from test_live_backend_rack_tools import _InsertTrack

from remote_script.AbletonCliRemote.command_backend import CommandError, dispatch_command
from remote_script.AbletonCliRemote.live_backend import LiveBackend


def _backend_with_return_track() -> tuple[LiveBackend, _InsertTrack]:
    surface = _SurfaceStub()
    track = _InsertTrack()
    track.name = "A-Reverb"
    track.devices = [
        _Device(
            "Echo",
            "Echo",
            [
                _Parameter("Device On", 1.0, is_quantized=True, value_items=("Off", "On")),
                _Parameter("Feedback", 0.5),
            ],
        )
    ]
    surface.song().return_tracks[1] = track
    return LiveBackend(surface), track


def _args(**extra: Any) -> dict[str, Any]:
    return {"return_track": 1, **extra}


def test_return_track_name_set_renames_the_return_track() -> None:
    backend, track = _backend_with_return_track()

    result = dispatch_command(backend, "return_track_name_set", _args(name="B Dub"))

    assert track.name == "B Dub"
    assert result == {"return_track": 1, "name": "B Dub"}


def test_return_track_devices_list_lists_devices() -> None:
    backend, _track = _backend_with_return_track()

    result = dispatch_command(backend, "return_track_devices_list", _args())

    assert result == {
        "return_track": 1,
        "devices": [{"index": 0, "name": "Echo", "class_name": "Echo"}],
    }


def test_return_track_device_insert_places_native_device() -> None:
    backend, track = _backend_with_return_track()

    result = dispatch_command(
        backend, "return_track_device_insert", _args(device_name="Saturator", index=0)
    )

    assert [device.name for device in track.devices] == ["Saturator", "Echo"]
    assert result["return_track"] == 1
    assert result["index"] == 0
    assert [device["name"] for device in result["devices"]] == ["Saturator", "Echo"]


def test_return_track_device_insert_without_index_appends() -> None:
    backend, track = _backend_with_return_track()

    result = dispatch_command(
        backend, "return_track_device_insert", _args(device_name="Utility", index=None)
    )

    assert track.devices[-1].name == "Utility"
    assert result["index"] == 1


def test_return_track_device_insert_reports_unknown_device_name() -> None:
    backend, _track = _backend_with_return_track()

    with pytest.raises(CommandError) as exc_info:
        dispatch_command(
            backend, "return_track_device_insert", _args(device_name="Serum", index=None)
        )

    assert exc_info.value.code == "INVALID_ARGUMENT"
    assert "Serum" in exc_info.value.message


def test_return_track_device_parameters_list_shows_display_values() -> None:
    backend, _track = _backend_with_return_track()

    result = dispatch_command(backend, "return_track_device_parameters_list", _args(device=0))

    assert result["return_track"] == 1
    assert result["device"] == 0
    assert result["device_name"] == "Echo"
    assert [p["name"] for p in result["parameters"]] == ["Device On", "Feedback"]
    assert result["parameters"][0]["display_value"] == "On"
    assert result["parameters"][0]["value_items"] == ["Off", "On"]


def test_return_track_device_parameter_set_display_sets_item() -> None:
    backend, track = _backend_with_return_track()

    result = dispatch_command(
        backend,
        "return_track_device_parameter_set_display",
        _args(device=0, parameter="Device On", display="Off"),
    )

    assert track.devices[0].parameters[0].value == 0.0
    assert result["parameter"] == 0
    assert result["display_value"] == "Off"


def test_return_track_device_parameter_set_display_rejects_unknown_parameter() -> None:
    backend, _track = _backend_with_return_track()

    with pytest.raises(CommandError) as exc_info:
        dispatch_command(
            backend,
            "return_track_device_parameter_set_display",
            _args(device=0, parameter="Nope", display="Off"),
        )

    assert exc_info.value.code == "INVALID_ARGUMENT"


def test_return_track_device_rejects_out_of_range_device() -> None:
    backend, _track = _backend_with_return_track()

    with pytest.raises(CommandError) as exc_info:
        dispatch_command(backend, "return_track_device_parameters_list", _args(device=3))

    assert exc_info.value.code == "INVALID_ARGUMENT"
