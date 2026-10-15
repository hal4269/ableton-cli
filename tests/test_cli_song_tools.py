from __future__ import annotations

import json
from typing import Any

import pytest

_MODULES = ("arrangement", "device", "clip", "tracks", "scenes", "return_tracks", "transport")


class _RecordingClient:
    def __init__(self) -> None:
        self.calls: list[tuple[str, tuple[Any, ...], dict[str, Any]]] = []

    def __getattr__(self, name: str):  # noqa: ANN204
        def _call(*args: Any, **kwargs: Any) -> dict[str, Any]:
            self.calls.append((name, args, kwargs))
            return {"called": name}

        return _call


@pytest.fixture
def client(monkeypatch: pytest.MonkeyPatch) -> _RecordingClient:
    import importlib

    recording = _RecordingClient()
    for module_name in _MODULES:
        module = importlib.import_module(f"ableton_cli.commands.{module_name}")
        monkeypatch.setattr(module, "get_client", lambda ctx: recording)
    runtime = importlib.import_module("ableton_cli.commands.track")
    monkeypatch.setattr(runtime, "get_client", lambda ctx: recording)
    return recording


_TRACK0 = {"mode": "index", "index": 0}
_DEVICE1 = {"mode": "index", "index": 1}
_DEVICE_SELECTORS = ["--track-index", "0", "--device-index", "1"]


@pytest.mark.parametrize(
    ("argv", "method", "expected"),
    [
        (
            ["device", "delete", *_DEVICE_SELECTORS],
            "device_delete",
            {"track_ref": _TRACK0, "device_ref": _DEVICE1},
        ),
        (
            ["device", "move", "--to-index", "2", *_DEVICE_SELECTORS],
            "device_move",
            {"track_ref": _TRACK0, "device_ref": _DEVICE1, "to_index": 2},
        ),
        (
            ["device", "enabled", "set", "false", *_DEVICE_SELECTORS],
            "device_enabled_set",
            {"track_ref": _TRACK0, "device_ref": _DEVICE1, "value": False},
        ),
        (
            ["device", "parameter", "list", *_DEVICE_SELECTORS],
            "device_parameters_list",
            {"track_ref": _TRACK0, "device_ref": _DEVICE1},
        ),
        (["clip", "color", "set", "0", "3", "12"], "clip_color_set", (0, 3, 12)),
        (["clip", "launch", "get", "0", "3"], "clip_launch_get", (0, 3)),
        (
            ["clip", "launch", "set", "0", "3", "--mode", "Gate", "--quantization", "1/16t"],
            "clip_launch_set",
            (0, 3, {"launch_mode": 1, "launch_quantization": 13}),
        ),
        (
            ["clip", "launch", "set", "0", "3", "--no-legato", "--velocity-amount", "0.5"],
            "clip_launch_set",
            (0, 3, {"legato": False, "velocity_amount": 0.5}),
        ),
        (["tracks", "duplicate", "2"], "tracks_duplicate", {"track": 2}),
        (["scenes", "duplicate", "1"], "scenes_duplicate", (1,)),
        (["scenes", "delete", "1"], "scenes_delete", (1,)),
        (["return-tracks", "create"], "return_tracks_create", {}),
        (["return-tracks", "delete", "1"], "return_tracks_delete", {"index": 1}),
        (["arrangement", "locator", "list"], "locators_list", {}),
        (
            ["arrangement", "locator", "add", "64", "--name", "Drop"],
            "locator_add",
            {"time": 64.0, "name": "Drop"},
        ),
        (["arrangement", "locator", "add", "0"], "locator_add", {"time": 0.0, "name": None}),
        (["arrangement", "locator", "delete", "0"], "locator_delete", {"index": 0}),
        (
            ["transport", "signature", "set", "7", "8"],
            "transport_signature_set",
            {"numerator": 7, "denominator": 8},
        ),
        (
            ["track", "color", "set", "5", "--track-name", "Bass"],
            "track_color_set",
            ({"mode": "name", "name": "Bass"}, 5),
        ),
    ],
)
def test_song_tool_commands_call_the_client(
    runner, cli_app, client: _RecordingClient, argv: list[str], method: str, expected: Any
) -> None:
    result = runner.invoke(cli_app, ["--output", "json", *argv])

    assert result.exit_code == 0, result.output
    assert json.loads(result.stdout)["result"] == {"called": method}
    [(name, args, kwargs)] = client.calls
    assert name == method
    if isinstance(expected, dict):
        assert kwargs == expected
    else:
        assert args == expected


@pytest.mark.parametrize(
    "argv",
    [
        ["clip", "color", "set", "0", "3", "70"],
        ["clip", "launch", "set", "0", "3"],
        ["clip", "launch", "set", "0", "3", "--mode", "loop"],
        ["clip", "launch", "set", "0", "3", "--velocity-amount", "2"],
        ["transport", "signature", "set", "4", "3"],
        ["track", "color", "set", "--track-index", "0", "--", "-1"],
        ["arrangement", "locator", "add", "--", "-4"],
        ["return-tracks", "delete", "--", "-1"],
    ],
)
def test_song_tool_commands_reject_invalid_input(
    runner, cli_app, client: _RecordingClient, argv: list[str]
) -> None:
    result = runner.invoke(cli_app, ["--output", "json", *argv])

    assert result.exit_code == 2, result.output
    assert json.loads(result.stdout)["error"]["code"] == "INVALID_ARGUMENT"
    assert client.calls == []
