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
        (
            ["device", "chains", "get", "2", *_DEVICE_SELECTORS],
            "device_chain_get",
            {"track_ref": _TRACK0, "device_ref": _DEVICE1, "chain_index": 2},
        ),
        (
            [
                "device",
                "chains",
                "set",
                "2",
                "--volume",
                "0.7",
                "--panning",
                "-0.5",
                "--mute",
                "--choke-group",
                "1",
                *_DEVICE_SELECTORS,
            ],
            "device_chain_set",
            {
                "track_ref": _TRACK0,
                "device_ref": _DEVICE1,
                "chain_index": 2,
                "settings": {"volume": 0.7, "panning": -0.5, "mute": True, "choke_group": 1},
            },
        ),
        (
            ["device", "chains", "set", "0", "--no-solo", *_DEVICE_SELECTORS],
            "device_chain_set",
            {
                "track_ref": _TRACK0,
                "device_ref": _DEVICE1,
                "chain_index": 0,
                "settings": {"solo": False},
            },
        ),
        (
            ["device", "variation", "list", *_DEVICE_SELECTORS],
            "device_variations_list",
            {"track_ref": _TRACK0, "device_ref": _DEVICE1},
        ),
        (
            ["device", "variation", "store", *_DEVICE_SELECTORS],
            "device_variation_store",
            {"track_ref": _TRACK0, "device_ref": _DEVICE1},
        ),
        (
            ["device", "variation", "recall", "1", *_DEVICE_SELECTORS],
            "device_variation_recall",
            {"track_ref": _TRACK0, "device_ref": _DEVICE1, "variation_index": 1},
        ),
        (
            ["device", "variation", "delete", "0", *_DEVICE_SELECTORS],
            "device_variation_delete",
            {"track_ref": _TRACK0, "device_ref": _DEVICE1, "variation_index": 0},
        ),
        (
            ["device", "insert", "Saturator", "--track-index", "0", "--index", "1"],
            "device_insert",
            {"track_ref": _TRACK0, "device_name": "Saturator", "index": 1},
        ),
        (
            ["device", "insert", "EQ Eight", "--track-name", "Bass"],
            "device_insert",
            {
                "track_ref": {"mode": "name", "name": "Bass"},
                "device_name": "EQ Eight",
                "index": None,
            },
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
            ["transport", "signature", "set", "7", "8"],
            "transport_signature_set",
            {"numerator": 7, "denominator": 8},
        ),
        (
            ["track", "color", "set", "5", "--track-name", "Bass"],
            "track_color_set",
            ({"mode": "name", "name": "Bass"}, 5),
        ),
        (["clip", "crop", "0", "3"], "clip_crop", (0, 3)),
        (["clip", "duplicate-loop", "0", "3"], "clip_duplicate_loop", (0, 3)),
        (["clip", "signature", "set", "0", "3", "7", "8"], "clip_signature_set", (0, 3, 7, 8)),
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
        ["clip", "signature", "set", "0", "3", "0", "4"],
        ["clip", "signature", "set", "0", "3", "4", "32"],
        ["clip", "crop", "--", "-1", "0"],
        ["track", "color", "set", "--track-index", "0", "--", "-1"],
        ["arrangement", "locator", "add", "--", "-4"],
        ["return-tracks", "delete", "--", "-1"],
        ["device", "chains", "set", "0", *_DEVICE_SELECTORS],
        ["device", "chains", "set", "0", "--choke-group", "17", *_DEVICE_SELECTORS],
        ["device", "chains", "get", *_DEVICE_SELECTORS, "--", "-1"],
        ["device", "variation", "recall", *_DEVICE_SELECTORS, "--", "-1"],
        ["device", "insert", "Utility", "--track-index", "0", "--index", "-1"],
        ["device", "insert", " ", "--track-index", "0"],
    ],
)
def test_song_tool_commands_reject_invalid_input(
    runner, cli_app, client: _RecordingClient, argv: list[str]
) -> None:
    result = runner.invoke(cli_app, ["--output", "json", *argv])

    assert result.exit_code == 2, result.output
    assert json.loads(result.stdout)["error"]["code"] == "INVALID_ARGUMENT"
    assert client.calls == []


class _LocatorClient:
    """Fakes Live's deferred playhead: a position set is reported after ``lag`` reads."""

    def __init__(self, *, lag: int = 2, is_playing: bool = False) -> None:
        self.calls: list[tuple[str, dict[str, Any]]] = []
        self.lag = lag
        self.is_playing = is_playing
        self.position = 0.0
        self.pending: float | None = None
        self.reads_until_applied = 0

    def song_info(self) -> dict[str, Any]:
        self.calls.append(("song_info", {}))
        return {"is_playing": self.is_playing, "current_time": self.position}

    def transport_position_set(self, beats: float) -> dict[str, Any]:
        self.calls.append(("transport_position_set", {"beats": beats}))
        self.pending = beats
        self.reads_until_applied = self.lag
        return {"current_time": self.position, "beat_position": self.position}

    def transport_position_get(self) -> dict[str, Any]:
        self.calls.append(("transport_position_get", {}))
        if self.pending is not None:
            if self.reads_until_applied == 0:
                self.position, self.pending = self.pending, None
            else:
                self.reads_until_applied -= 1
        return {"current_time": self.position, "beat_position": self.position}

    def locators_list(self) -> dict[str, Any]:
        self.calls.append(("locators_list", {}))
        locators = [
            {"index": 0, "name": "Intro", "time": 0.0},
            {"index": 1, "name": "Drop", "time": 64.0},
        ]
        return {"locator_count": 2, "locators": locators}

    def locator_add(self, time: float, name: str | None) -> dict[str, Any]:
        self.calls.append(("locator_add", {"time": time, "name": name, "at": self.position}))
        return {"index": 0, "name": name, "time": time}

    def locator_delete(self, index: int) -> dict[str, Any]:
        self.calls.append(("locator_delete", {"index": index, "at": self.position}))
        return {"index": index, "name": "Drop", "time": 64.0, "deleted": True}


@pytest.fixture
def locator_client(monkeypatch: pytest.MonkeyPatch) -> _LocatorClient:
    from ableton_cli.commands import _arrangement_locator_commands, arrangement

    fake = _LocatorClient()
    monkeypatch.setattr(arrangement, "get_client", lambda ctx: fake)
    monkeypatch.setattr(_arrangement_locator_commands, "_sleep", lambda seconds: None)
    return fake


def _names(client: _LocatorClient) -> list[str]:
    return [name for name, _ in client.calls]


def test_locator_add_moves_the_playhead_and_waits_until_live_applies_it(
    runner, cli_app, locator_client: _LocatorClient
) -> None:
    result = runner.invoke(
        cli_app, ["--output", "json", "arrangement", "locator", "add", "64", "--name", "Drop"]
    )

    assert result.exit_code == 0, result.output
    assert json.loads(result.stdout)["result"] == {"index": 0, "name": "Drop", "time": 64.0}
    assert _names(locator_client) == [
        "song_info",
        "transport_position_set",
        "transport_position_get",
        "transport_position_get",
        "transport_position_get",
        "locator_add",
    ]
    assert locator_client.calls[1] == ("transport_position_set", {"beats": 64.0})
    assert locator_client.calls[-1] == ("locator_add", {"time": 64.0, "name": "Drop", "at": 64.0})


def test_locator_delete_moves_the_playhead_onto_the_locator_first(
    runner, cli_app, locator_client: _LocatorClient
) -> None:
    result = runner.invoke(cli_app, ["--output", "json", "arrangement", "locator", "delete", "1"])

    assert result.exit_code == 0, result.output
    assert json.loads(result.stdout)["result"] == {
        "index": 1,
        "name": "Drop",
        "time": 64.0,
        "deleted": True,
    }
    assert _names(locator_client)[:3] == ["song_info", "locators_list", "transport_position_set"]
    assert locator_client.calls[2] == ("transport_position_set", {"beats": 64.0})
    assert locator_client.calls[-1] == ("locator_delete", {"index": 1, "at": 64.0})


def test_locator_delete_rejects_an_unknown_index_before_moving_the_playhead(
    runner, cli_app, locator_client: _LocatorClient
) -> None:
    result = runner.invoke(cli_app, ["--output", "json", "arrangement", "locator", "delete", "2"])

    assert result.exit_code == 2, result.output
    assert json.loads(result.stdout)["error"]["code"] == "INVALID_ARGUMENT"
    assert _names(locator_client) == ["song_info", "locators_list"]


@pytest.mark.parametrize(
    "argv",
    [["arrangement", "locator", "add", "16"], ["arrangement", "locator", "delete", "0"]],
)
def test_locator_commands_refuse_to_move_a_playing_transport(
    runner, cli_app, locator_client: _LocatorClient, argv: list[str]
) -> None:
    locator_client.is_playing = True

    result = runner.invoke(cli_app, ["--output", "json", *argv])

    assert result.exit_code == 2, result.output
    payload = json.loads(result.stdout)
    assert payload["error"]["code"] == "INVALID_ARGUMENT"
    assert "transport stop" in payload["error"]["hint"]
    assert _names(locator_client) == ["song_info"]


def test_locator_add_times_out_when_live_never_applies_the_playhead(
    runner, cli_app, locator_client: _LocatorClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    from ableton_cli.commands import _arrangement_locator_commands

    clock = iter(float(tick) for tick in range(1000))
    monkeypatch.setattr(_arrangement_locator_commands, "_monotonic", lambda: next(clock))
    locator_client.lag = 10_000

    result = runner.invoke(cli_app, ["--output", "json", "arrangement", "locator", "add", "16"])

    assert result.exit_code == 12, result.output
    error = json.loads(result.stdout)["error"]
    assert error["code"] == "TIMEOUT"
    assert "16.0" in error["message"]
    assert "locator_add" not in _names(locator_client)


_POINTS_JSON = '[{"time": 0.0, "value": 0.2}, {"time": 4.0, "value": 0.8}]'
_POINTS = [{"time": 0.0, "value": 0.2}, {"time": 4.0, "value": 0.8}]


@pytest.mark.parametrize(
    ("target", "mixer", "send_index"),
    [
        (["volume"], "volume", None),
        (["Panning"], "panning", None),
        (["send", "--send-index", "1"], "send", 1),
    ],
)
def test_clip_envelope_mixer_set_targets_the_mixer(
    runner,
    cli_app,
    client: _RecordingClient,
    target: list[str],
    mixer: str,
    send_index: int | None,
) -> None:
    argv = ["clip", "envelope", "mixer", "set", "0", "3", *target, "--points-json", _POINTS_JSON]

    result = runner.invoke(cli_app, ["--output", "json", *argv])

    assert result.exit_code == 0, result.output
    [(name, args, kwargs)] = client.calls
    assert name == "clip_envelope_set"
    assert args == (0, 3, None, None, _POINTS, "replace")
    assert kwargs == {"mixer": mixer, "send_index": send_index}


def test_clip_envelope_mixer_shape_writes_generated_points(
    runner, cli_app, client: _RecordingClient
) -> None:
    argv = [
        "clip", "envelope", "mixer", "shape", "0", "3", "volume", "--shape", "ramp",
        "--from", "0", "--to", "0.85", "--length", "4", "--resolution", "2",
    ]  # fmt: skip

    result = runner.invoke(cli_app, ["--output", "json", *argv])

    assert result.exit_code == 0, result.output
    [(name, args, kwargs)] = client.calls
    assert name == "clip_envelope_set"
    assert args[:4] == (0, 3, None, None)
    assert args[4][0]["value"] == 0.0
    assert args[4][-1]["value"] == 0.85
    assert kwargs == {"mixer": "volume", "send_index": None}


def test_clip_envelope_mixer_clear_targets_one_mixer_parameter(
    runner, cli_app, client: _RecordingClient
) -> None:
    argv = ["clip", "envelope", "mixer", "clear", "0", "3", "send", "--send-index", "0"]

    result = runner.invoke(cli_app, ["--output", "json", *argv])

    assert result.exit_code == 0, result.output
    assert client.calls == [
        ("clip_envelope_clear", (0, 3), {"clear_all": False, "mixer": "send", "send_index": 0})
    ]


@pytest.mark.parametrize(
    "argv",
    [
        ["clip", "envelope", "mixer", "set", "0", "3", "volume", "--send-index", "0"],
        ["clip", "envelope", "mixer", "set", "0", "3", "send"],
        ["clip", "envelope", "mixer", "set", "0", "3", "send", "--send-index", "-1"],
        ["clip", "envelope", "mixer", "set", "0", "3", "crossfader"],
        ["clip", "envelope", "mixer", "clear", "0", "3", "send"],
        ["clip", "envelope", "mixer", "shape", "0", "3", "volume", "--shape", "saw",
         "--from", "0", "--to", "1"],
    ],
)  # fmt: skip
def test_clip_envelope_mixer_rejects_invalid_targets(
    runner, cli_app, client: _RecordingClient, argv: list[str]
) -> None:
    if argv[3] == "set":
        argv = [*argv, "--points-json", _POINTS_JSON]

    result = runner.invoke(cli_app, ["--output", "json", *argv])

    assert result.exit_code == 2, result.output
    assert json.loads(result.stdout)["error"]["code"] == "INVALID_ARGUMENT"
    assert client.calls == []
