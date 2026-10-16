from __future__ import annotations

from typing import Any

import pytest
from test_live_backend import _Song, _SurfaceStub, _Track

from remote_script.AbletonCliRemote.command_backend import CommandError, dispatch_command
from remote_script.AbletonCliRemote.live_backend import LiveBackend
from remote_script.AbletonCliRemote.live_backend_parts import (
    song_settings as song_settings_module,
)


@pytest.fixture(autouse=True)
def _identity_recording_quantization(monkeypatch: pytest.MonkeyPatch) -> None:
    """Live's RecordingQuantization enum is not importable outside Ableton."""
    monkeypatch.setattr(song_settings_module, "recording_quantization_value", lambda index: index)


def _backend() -> tuple[LiveBackend, _Song, _SurfaceStub]:
    surface = _SurfaceStub()
    return LiveBackend(surface), surface.song(), surface


def _track_ref(index: int) -> dict[str, Any]:
    return {"mode": "index", "index": index}


def _invalid(backend: LiveBackend, name: str, args: dict[str, Any]) -> CommandError:
    with pytest.raises(CommandError) as exc_info:
        dispatch_command(backend, name, args)
    assert exc_info.value.code == "INVALID_ARGUMENT"
    return exc_info.value


def _group_song(song: _Song) -> None:
    """Track 0 becomes a folded group containing track 1."""
    group = _Track(name="Drums", has_audio_input=True, has_midi_input=False)
    group.is_foldable = True
    group.fold_state = 1
    song.tracks.insert(0, group)
    song.tracks[1].is_grouped = True
    song.tracks[1].group_track = group


# --- Back to Arrangement ----------------------------------------------------------


def test_back_to_arranger_clears_the_button() -> None:
    backend, song, _ = _backend()
    song.back_to_arranger = True

    result = dispatch_command(backend, "back_to_arranger", {})

    assert result == {"back_to_arranger": False}
    assert song.back_to_arranger is False


def test_song_info_reports_song_settings() -> None:
    backend, song, _ = _backend()
    song.back_to_arranger = True
    song.loop = True
    song.loop_start = 8.0
    song.loop_length = 32.0
    song.metronome = True
    song.swing_amount = 0.25
    song.root_note = 9
    song.scale_name = "Minor"
    song.scale_mode = True
    song.scale_intervals = [0, 2, 3, 5, 7, 8, 10]
    song.midi_recording_quantization = 5

    info = dispatch_command(backend, "song_info", {})

    assert info["back_to_arranger"] is True
    assert info["loop"] == {"enabled": True, "start": 8.0, "length": 32.0, "end": 40.0}
    assert info["metronome"] is True
    assert info["swing_amount"] == 0.25
    assert info["groove_amount"] == 1.0
    assert info["scale"] == {
        "root_note": 9,
        "root_name": "A",
        "name": "Minor",
        "mode": True,
        "intervals": [0, 2, 3, 5, 7, 8, 10],
    }
    assert info["midi_recording_quantization"] == "1/16"
    assert info["can_capture_midi"] is False


# --- Song settings ----------------------------------------------------------------


def test_song_loop_set_changes_only_given_fields() -> None:
    backend, song, _ = _backend()

    result = dispatch_command(
        backend, "song_loop_set", {"settings": {"enabled": True, "start": 16.0}}
    )

    assert result == {"enabled": True, "start": 16.0, "length": 16.0, "end": 32.0}
    assert dispatch_command(backend, "song_loop_get", {}) == result
    assert song.loop is True


@pytest.mark.parametrize(
    "settings",
    [{}, {"start": -1.0}, {"length": 0.0}, {"enabled": "yes"}, {"end": 4.0}],
)
def test_song_loop_set_rejects_invalid_settings(settings: dict[str, Any]) -> None:
    backend, _, _ = _backend()
    _invalid(backend, "song_loop_set", {"settings": settings})


def test_song_metronome_swing_and_groove_amount_set() -> None:
    backend, song, _ = _backend()

    assert dispatch_command(backend, "song_metronome_set", {"value": True}) == {"metronome": True}
    assert dispatch_command(backend, "song_swing_set", {"value": 0.5}) == {"swing_amount": 0.5}
    assert dispatch_command(backend, "song_groove_amount_set", {"value": 1.3}) == {
        "groove_amount": 1.3
    }
    assert (song.metronome, song.swing_amount, song.groove_amount) == (True, 0.5, 1.3)
    _invalid(backend, "song_swing_set", {"value": 1.5})
    _invalid(backend, "song_groove_amount_set", {"value": -0.1})


def test_song_scale_set_updates_given_fields() -> None:
    backend, song, _ = _backend()

    result = dispatch_command(
        backend, "song_scale_set", {"settings": {"root_note": 2, "name": "Dorian", "mode": True}}
    )

    assert result["root_note"] == 2
    assert result["root_name"] == "D"
    assert result["name"] == "Dorian"
    assert result["mode"] is True
    assert (song.root_note, song.scale_name, song.scale_mode) == (2, "Dorian", True)
    _invalid(backend, "song_scale_set", {"settings": {"root_note": 12}})
    _invalid(backend, "song_scale_set", {"settings": {"name": " "}})
    _invalid(backend, "song_scale_set", {"settings": {}})


def test_song_record_quantization_set_maps_names_to_live_values() -> None:
    backend, song, _ = _backend()

    result = dispatch_command(backend, "song_record_quantization_set", {"value": "1/16t"})

    assert result == {"midi_recording_quantization": "1/16t"}
    assert song.midi_recording_quantization == 6
    _invalid(backend, "song_record_quantization_set", {"value": "1/64"})


def test_song_capture_midi_requires_something_to_capture() -> None:
    backend, song, _ = _backend()

    _invalid(backend, "song_capture_midi", {"destination": "auto"})
    song.can_capture_midi = True
    result = dispatch_command(backend, "song_capture_midi", {"destination": "arrangement"})

    assert result == {"captured": True, "destination": "arrangement"}
    assert song.capture_midi_calls == [2]
    _invalid(backend, "song_capture_midi", {"destination": "clip"})


# --- Scene tempo and signature ----------------------------------------------------


def test_scene_tempo_set_and_clear() -> None:
    backend, song, _ = _backend()

    assert dispatch_command(backend, "scene_tempo_set", {"scene": 1, "bpm": 128.0}) == {
        "scene": 1,
        "tempo": 128.0,
    }
    assert (song.scenes[1].tempo, song.scenes[1].tempo_enabled) == (128.0, True)
    listed = dispatch_command(backend, "scenes_list", {})["scenes"]
    assert listed[1]["tempo"] == 128.0
    assert listed[0]["tempo"] is None

    assert dispatch_command(backend, "scene_tempo_set", {"scene": 1, "bpm": None}) == {
        "scene": 1,
        "tempo": None,
    }
    assert song.scenes[1].tempo_enabled is False
    _invalid(backend, "scene_tempo_set", {"scene": 1, "bpm": 5.0})
    _invalid(backend, "scene_tempo_set", {"scene": 9, "bpm": 120.0})


def test_scene_signature_set_and_clear() -> None:
    backend, song, _ = _backend()

    result = dispatch_command(
        backend, "scene_signature_set", {"scene": 0, "numerator": 7, "denominator": 8}
    )

    assert result == {"scene": 0, "signature": {"numerator": 7, "denominator": 8}}
    assert song.scenes[0].time_signature_enabled is True
    assert dispatch_command(backend, "scenes_list", {})["scenes"][0]["signature"] == {
        "numerator": 7,
        "denominator": 8,
    }
    cleared = dispatch_command(
        backend, "scene_signature_set", {"scene": 0, "numerator": None, "denominator": None}
    )
    assert cleared == {"scene": 0, "signature": None}
    assert song.scenes[0].time_signature_enabled is False
    _invalid(backend, "scene_signature_set", {"scene": 0, "numerator": 4, "denominator": 3})
    _invalid(backend, "scene_signature_set", {"scene": 0, "numerator": 4, "denominator": None})


# --- Track monitoring and groups --------------------------------------------------


def test_track_monitoring_get_and_set() -> None:
    backend, song, _ = _backend()

    assert dispatch_command(backend, "track_monitoring_get", {"track_ref": _track_ref(1)}) == {
        "track": 1,
        "monitoring": "auto",
    }
    result = dispatch_command(
        backend, "track_monitoring_set", {"track_ref": _track_ref(1), "value": "in"}
    )

    assert result == {"track": 1, "monitoring": "in"}
    assert song.tracks[1].current_monitoring_state == 0
    _invalid(backend, "track_monitoring_set", {"track_ref": _track_ref(1), "value": "on"})


def test_track_monitoring_fails_clearly_on_group_tracks() -> None:
    backend, song, _ = _backend()
    _group_song(song)

    error = _invalid(backend, "track_monitoring_get", {"track_ref": _track_ref(0)})

    assert "group track" in error.message
    _invalid(backend, "track_monitoring_set", {"track_ref": _track_ref(0), "value": "off"})


def test_tracks_list_and_track_info_report_group_state() -> None:
    backend, song, _ = _backend()
    _group_song(song)

    tracks = dispatch_command(backend, "tracks_list", {})["tracks"]
    info = dispatch_command(backend, "get_track_info", {"track_ref": _track_ref(1)})

    assert {key: tracks[0][key] for key in ("is_foldable", "fold_state", "is_grouped")} == {
        "is_foldable": True,
        "fold_state": True,
        "is_grouped": False,
    }
    assert tracks[0]["group_track"] is None
    assert tracks[1]["fold_state"] is None
    assert tracks[1]["is_grouped"] is True
    assert tracks[1]["group_track"] == 0
    assert info["group_track"] == 0
    assert info["is_foldable"] is False


def test_track_fold_set_only_on_group_tracks() -> None:
    backend, song, _ = _backend()
    _group_song(song)

    result = dispatch_command(
        backend, "track_fold_set", {"track_ref": _track_ref(0), "value": False}
    )

    assert result == {"track": 0, "fold_state": False}
    assert song.tracks[0].fold_state == 0
    _invalid(backend, "track_fold_set", {"track_ref": _track_ref(1), "value": True})


# --- View -------------------------------------------------------------------------


def test_view_show_focuses_live_view_names() -> None:
    backend, _, surface = _backend()

    result = dispatch_command(backend, "view_show", {"view": "device-chain"})

    assert result == {"view": "device-chain", "live_view": "Detail/DeviceChain", "visible": True}
    assert surface.application().view.focused_views == ["Detail/DeviceChain"]
    _invalid(backend, "view_show", {"view": "mixer"})


def test_view_select_track_scene_and_clip() -> None:
    backend, song, _ = _backend()
    song.tracks[1].clip_slots[1].create_clip(4.0)

    assert dispatch_command(backend, "view_select_track", {"track": 1}) == {
        "track": 1,
        "name": "Track 2",
    }
    assert song.view.selected_track is song.tracks[1]
    assert dispatch_command(backend, "view_select_scene", {"scene": 1}) == {
        "scene": 1,
        "name": "Scene 2",
    }
    assert song.view.selected_scene is song.scenes[1]

    result = dispatch_command(backend, "view_select_clip", {"track": 1, "clip": 1})

    assert result == {"track": 1, "clip": 1, "has_clip": True}
    assert song.view.highlighted_clip_slot is song.tracks[1].clip_slots[1]
    assert song.view.detail_clip is song.tracks[1].clip_slots[1].clip
    _invalid(backend, "view_select_track", {"track": 5})
    _invalid(backend, "view_select_clip", {"track": 0, "clip": 7})
