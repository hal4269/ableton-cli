from __future__ import annotations

import json
from typing import Any

import pytest

_MODULES = ("arrangement", "song", "scenes", "track", "view")


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
    return recording


_TRACK2 = {"mode": "index", "index": 2}


@pytest.mark.parametrize(
    ("argv", "method", "expected"),
    [
        (["arrangement", "back-to-arranger"], "back_to_arranger", {}),
        (["song", "loop", "get"], "song_loop_get", {}),
        (
            ["song", "loop", "set", "--enabled", "--start", "16", "--length", "32"],
            "song_loop_set",
            {"settings": {"enabled": True, "start": 16.0, "length": 32.0}},
        ),
        (["song", "loop", "set", "--disabled"], "song_loop_set", {"settings": {"enabled": False}}),
        (["song", "metronome", "set", "true"], "song_metronome_set", {"value": True}),
        (["song", "swing", "set", "0.25"], "song_swing_set", {"value": 0.25}),
        (["song", "groove-amount", "set", "1.3"], "song_groove_amount_set", {"value": 1.3}),
        (
            ["song", "scale", "set", "--root", "A", "--name", "Minor", "--mode"],
            "song_scale_set",
            {"settings": {"root_note": 9, "name": "Minor", "mode": True}},
        ),
        (
            ["song", "scale", "set", "--root", "Bb"],
            "song_scale_set",
            {"settings": {"root_note": 10}},
        ),
        (["song", "scale", "set", "--root", "2"], "song_scale_set", {"settings": {"root_note": 2}}),
        (["song", "scale", "set", "--no-mode"], "song_scale_set", {"settings": {"mode": False}}),
        (
            ["song", "record-quantization", "set", "1/16"],
            "song_record_quantization_set",
            {"value": "1/16"},
        ),
        (["song", "capture-midi"], "song_capture_midi", {"destination": "auto"}),
        (
            ["song", "capture-midi", "--destination", "arrangement"],
            "song_capture_midi",
            {"destination": "arrangement"},
        ),
        (["scenes", "tempo", "set", "1", "128"], "scene_tempo_set", {"scene": 1, "bpm": 128.0}),
        (["scenes", "tempo", "set", "1", "--clear"], "scene_tempo_set", {"scene": 1, "bpm": None}),
        (
            ["scenes", "signature", "set", "0", "7", "8"],
            "scene_signature_set",
            {"scene": 0, "numerator": 7, "denominator": 8},
        ),
        (
            ["scenes", "signature", "set", "0", "--clear"],
            "scene_signature_set",
            {"scene": 0, "numerator": None, "denominator": None},
        ),
        (
            ["track", "monitoring", "get", "--track-index", "2"],
            "track_monitoring_get",
            (_TRACK2,),
        ),
        (
            ["track", "monitoring", "set", "off", "--track-index", "2"],
            "track_monitoring_set",
            (_TRACK2, "off"),
        ),
        (
            ["track", "fold", "set", "false", "--track-index", "2"],
            "track_fold_set",
            (_TRACK2, False),
        ),
        (["view", "show", "device-chain"], "view_show", {"view": "device-chain"}),
        (["view", "select", "track", "3"], "view_select_track", {"track": 3}),
        (["view", "select", "scene", "1"], "view_select_scene", {"scene": 1}),
        (["view", "select", "clip", "3", "1"], "view_select_clip", {"track": 3, "clip": 1}),
    ],
)
def test_song_setting_commands_call_the_client(
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
        ["song", "loop", "set"],
        ["song", "loop", "set", "--start", "-1"],
        ["song", "loop", "set", "--length", "0"],
        ["song", "swing", "set", "1.5"],
        ["song", "groove-amount", "set", "2"],
        ["song", "scale", "set"],
        ["song", "scale", "set", "--root", "H"],
        ["song", "scale", "set", "--root", "12"],
        ["song", "scale", "set", "--name", " "],
        ["song", "record-quantization", "set", "1/64"],
        ["song", "capture-midi", "--destination", "clip"],
        ["scenes", "tempo", "set", "1"],
        ["scenes", "tempo", "set", "1", "128", "--clear"],
        ["scenes", "tempo", "set", "1", "5"],
        ["scenes", "signature", "set", "0", "7"],
        ["scenes", "signature", "set", "0", "4", "3"],
        ["scenes", "signature", "set", "0", "7", "8", "--clear"],
        ["track", "monitoring", "set", "on", "--track-index", "0"],
        ["view", "show", "mixer"],
        ["view", "select", "track", "--", "-1"],
    ],
)
def test_song_setting_commands_reject_invalid_input(
    runner, cli_app, client: _RecordingClient, argv: list[str]
) -> None:
    result = runner.invoke(cli_app, ["--output", "json", *argv])

    assert result.exit_code == 2, result.output
    assert json.loads(result.stdout)["error"]["code"] == "INVALID_ARGUMENT"
    assert client.calls == []


@pytest.mark.parametrize("argv", [["song", "save", "--path", "x.als"], ["song", "export", "audio"]])
def test_song_save_and_export_are_not_commands(runner, cli_app, argv: list[str]) -> None:
    result = runner.invoke(cli_app, ["--output", "json", *argv])

    assert result.exit_code != 0
