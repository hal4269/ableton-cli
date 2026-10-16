from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import pytest
from test_live_backend import _Chain, _Device, _Parameter, _Song, _SurfaceStub, _Track

from remote_script.AbletonCliRemote.command_backend import CommandError, dispatch_command
from remote_script.AbletonCliRemote.live_backend import LiveBackend


class _EditableTrack(_Track):
    """A track that also supports color and device deletion, like Live's Track."""

    def __init__(self, name: str) -> None:
        super().__init__(name=name, has_audio_input=False, has_midi_input=True)
        self.color_index = 0

    def delete_device(self, index: int) -> None:
        del self.devices[index]


class _EditableChain(_Chain):
    def delete_device(self, index: int) -> None:
        del self.devices[index]


@dataclass
class _CuePoint:
    name: str
    time: float


class _CuePointView:
    """Live hands out a fresh Python wrapper per access, so ``is`` never matches."""

    def __init__(self, cue: _CuePoint) -> None:
        self._cue = cue

    @property
    def name(self) -> str:
        return self._cue.name

    @name.setter
    def name(self, value: str) -> None:
        self._cue.name = value

    @property
    def time(self) -> float:
        return self._cue.time


class _StructureSong(_Song):
    def __init__(self) -> None:
        self.song_length = 256.0
        super().__init__()
        self.tracks = [_EditableTrack("Drums"), _EditableTrack("Bass")]
        self.view.selected_track = self.tracks[0]
        self.cues: list[_CuePoint] = []
        self.cue_toggle_times: list[float] = []

    @property
    def cue_points(self) -> list[_CuePointView]:
        return [_CuePointView(cue) for cue in self.cues]

    @property
    def current_song_time(self) -> float:
        return self._current_song_time

    @current_song_time.setter
    def current_song_time(self, value: float) -> None:
        if value > self.song_length:
            raise RuntimeError("Cannot set the Songtime behind the Songlength")
        self._current_song_time = float(value)

    def duplicate_track(self, index: int) -> None:
        copy = _EditableTrack(self.tracks[index].name)
        self.tracks.insert(index + 1, copy)

    def duplicate_scene(self, index: int) -> None:
        self.create_scene(index + 1)

    def delete_scene(self, index: int) -> None:
        del self.scenes[index]

    def create_return_track(self) -> None:
        self.return_tracks.append(
            _Track(name="C Return", has_audio_input=False, has_midi_input=False)
        )

    def delete_return_track(self, index: int) -> None:
        del self.return_tracks[index]

    def set_or_delete_cue(self) -> None:
        time = float(self.current_song_time)
        self.cue_toggle_times.append(time)
        for cue in self.cues:
            if cue.time == time:
                self.cues.remove(cue)
                return
        self.cues.append(_CuePoint(name=str(len(self.cues) + 1), time=time))

    def move_device(self, device: Any, target: Any, position: int) -> int:
        target.devices.remove(device)
        target.devices.insert(position, device)
        return position


class _StructureSurface(_SurfaceStub):
    def __init__(self) -> None:
        super().__init__()
        self._song_obj = _StructureSong()


def _backend() -> tuple[LiveBackend, _StructureSong]:
    surface = _StructureSurface()
    return LiveBackend(surface), surface.song()  # type: ignore[return-value]


def _device_args(track: int, device: int) -> dict[str, Any]:
    return {
        "track_ref": {"mode": "index", "index": track},
        "device_ref": {"mode": "index", "index": device},
    }


def _three_devices(song: _StructureSong) -> None:
    song.tracks[0].devices = [
        _Device("Operator", "Operator", [_Parameter("Device On", 1.0)]),
        _Device("Saturator", "Saturator", [_Parameter("Device On", 1.0), _Parameter("Drive", 0.2)]),
        _Device("Echo", "Echo", [_Parameter("Device On", 1.0)]),
    ]


def test_device_delete_removes_a_top_level_device() -> None:
    backend, song = _backend()
    _three_devices(song)

    result = dispatch_command(backend, "device_delete", _device_args(0, 1))

    assert result == {"track": 0, "device": 1, "deleted": True, "device_count": 2}
    assert [device.name for device in song.tracks[0].devices] == ["Operator", "Echo"]


def test_device_delete_reaches_a_device_inside_a_rack_chain() -> None:
    backend, song = _backend()
    chain = _EditableChain("Chain", devices=[_Device("Utility", "StereoGain", [])])
    song.tracks[0].devices = [
        _Device("Rack", "AudioEffectGroupDevice", [], can_have_chains=True, chains=[chain])
    ]
    nested_ref = backend.device_chains_list(0, 0)["chains"][0]["devices"][0]["stable_ref"]

    result = dispatch_command(
        backend,
        "device_delete",
        {
            "track_ref": {"mode": "index", "index": 0},
            "device_ref": {"mode": "stable_ref", "stable_ref": nested_ref},
        },
    )

    assert result["deleted"] is True
    assert chain.devices == []


def test_device_move_uses_song_move_device() -> None:
    backend, song = _backend()
    _three_devices(song)

    result = dispatch_command(backend, "device_move", {**_device_args(0, 2), "to_index": 1})

    assert result == {"track": 0, "device": 2, "to_index": 1}
    assert [device.name for device in song.tracks[0].devices] == ["Operator", "Echo", "Saturator"]


def test_device_move_rejects_out_of_range_destination() -> None:
    backend, song = _backend()
    _three_devices(song)

    with pytest.raises(CommandError) as exc_info:
        dispatch_command(backend, "device_move", {**_device_args(0, 0), "to_index": 3})

    assert exc_info.value.code == "INVALID_ARGUMENT"


def test_device_enabled_set_switches_device_on_parameter() -> None:
    backend, song = _backend()
    _three_devices(song)

    result = dispatch_command(backend, "device_enabled_set", {**_device_args(0, 1), "value": False})

    assert result == {"track": 0, "device": 1, "enabled": False}
    assert song.tracks[0].devices[1].parameters[0].value == 0.0


def test_device_enabled_set_fails_without_device_on_parameter() -> None:
    backend, _song = _backend()

    with pytest.raises(CommandError) as exc_info:
        dispatch_command(backend, "device_enabled_set", {**_device_args(0, 0), "value": True})

    assert exc_info.value.code == "INVALID_ARGUMENT"


def test_device_parameters_list_lists_every_parameter() -> None:
    backend, song = _backend()
    _three_devices(song)

    result = dispatch_command(backend, "device_parameters_list", _device_args(0, 1))

    assert result["device_name"] == "Saturator"
    assert [parameter["name"] for parameter in result["parameters"]] == ["Device On", "Drive"]
    assert result["parameters"][1]["value"] == 0.2


def test_track_and_clip_color_set() -> None:
    backend, song = _backend()
    song.tracks[1].clip_slots[0].create_clip(4.0)

    track_ref = {"mode": "name", "name": "Bass"}
    assert dispatch_command(
        backend, "track_color_set", {"track_ref": track_ref, "color_index": 12}
    ) == {
        "track": 1,
        "color_index": 12,
    }
    clip_result = dispatch_command(
        backend, "clip_color_set", {"track": 1, "clip": 0, "color_index": 69}
    )

    assert song.tracks[1].color_index == 12
    assert clip_result == {"track": 1, "clip": 0, "color_index": 69}
    with pytest.raises(CommandError):
        dispatch_command(backend, "track_color_set", {"track_ref": track_ref, "color_index": 70})


def test_clip_launch_set_changes_only_given_settings() -> None:
    backend, song = _backend()
    song.tracks[0].clip_slots[0].create_clip(4.0)
    clip = song.tracks[0].clip_slots[0].clip
    clip.launch_mode = 0
    clip.launch_quantization = 0
    clip.legato = False
    clip.velocity_amount = 0.0

    result = dispatch_command(
        backend,
        "clip_launch_set",
        {"track": 0, "clip": 0, "settings": {"launch_quantization": 5, "legato": True}},
    )

    assert result == {
        "track": 0,
        "clip": 0,
        "launch_mode": 0,
        "launch_quantization": 5,
        "legato": True,
        "velocity_amount": 0.0,
    }
    assert dispatch_command(backend, "clip_launch_get", {"track": 0, "clip": 0}) == result


@pytest.mark.parametrize(
    "settings",
    [{}, {"launch_mode": 4}, {"velocity_amount": 1.5}, {"follow_action": 1}],
)
def test_clip_launch_set_rejects_invalid_settings(settings: dict[str, Any]) -> None:
    backend, song = _backend()
    song.tracks[0].clip_slots[0].create_clip(4.0)

    with pytest.raises(CommandError) as exc_info:
        dispatch_command(backend, "clip_launch_set", {"track": 0, "clip": 0, "settings": settings})

    assert exc_info.value.code == "INVALID_ARGUMENT"


def test_tracks_duplicate_and_scene_duplicate_delete() -> None:
    backend, song = _backend()

    duplicated = dispatch_command(backend, "tracks_duplicate", {"track": 1})
    scene_copy = dispatch_command(backend, "scenes_duplicate", {"scene": 0})
    scene_deleted = dispatch_command(backend, "scenes_delete", {"scene": 2})

    assert duplicated == {"track": 1, "new_track": 2, "name": "Bass", "track_count": 3}
    assert scene_copy == {"scene": 0, "new_scene": 1, "scene_count": 3}
    assert scene_deleted == {"scene": 2, "deleted": True, "scene_count": 2}
    assert len(song.scenes) == 2


def test_return_tracks_create_and_delete() -> None:
    backend, song = _backend()

    created = dispatch_command(backend, "return_tracks_create", {})
    deleted = dispatch_command(backend, "return_tracks_delete", {"index": 0})

    assert created == {"index": 2, "name": "C Return", "return_track_count": 3}
    assert deleted == {"index": 0, "deleted": True, "return_track_count": 2}
    assert [track.name for track in song.return_tracks] == ["Delay", "C Return"]


def _move_playhead(backend: LiveBackend, beats: float) -> None:
    dispatch_command(backend, "transport_position_set", {"beats": beats})


def test_locators_add_list_delete_at_the_playhead_without_moving_it() -> None:
    backend, song = _backend()

    _move_playhead(backend, 64.0)
    added = dispatch_command(backend, "locator_add", {"time": 64.0, "name": "Drop"})
    _move_playhead(backend, 0.0)
    dispatch_command(backend, "locator_add", {"time": 0.0, "name": "Intro"})
    listed = dispatch_command(backend, "locators_list", {})
    _move_playhead(backend, 64.0)
    deleted = dispatch_command(backend, "locator_delete", {"index": 1})

    assert added == {"index": 0, "name": "Drop", "time": 64.0}
    assert listed["locators"] == [
        {"index": 0, "name": "Intro", "time": 0.0},
        {"index": 1, "name": "Drop", "time": 64.0},
    ]
    assert deleted == {"index": 1, "name": "Drop", "time": 64.0, "deleted": True}
    assert [cue.name for cue in song.cues] == ["Intro"]
    assert song.cue_toggle_times == [64.0, 0.0, 64.0]
    assert song.current_song_time == 64.0


def test_locator_add_returns_the_index_of_the_new_cue_among_existing_ones() -> None:
    backend, song = _backend()
    song.cues = [_CuePoint("A", 0.0), _CuePoint("C", 32.0)]

    _move_playhead(backend, 16.0)
    added = dispatch_command(backend, "locator_add", {"time": 16.0, "name": "B"})

    assert added == {"index": 1, "name": "B", "time": 16.0}


def test_locator_add_requires_the_playhead_at_the_locator_position() -> None:
    backend, song = _backend()
    _move_playhead(backend, 0.0)

    with pytest.raises(CommandError) as error:
        dispatch_command(backend, "locator_add", {"time": 4.0, "name": "Verse"})

    assert error.value.code == "INVALID_ARGUMENT"
    assert "transport position set 4.0" in str(error.value.hint)
    assert song.cue_toggle_times == []
    assert song.current_song_time == 0.0


def test_locator_delete_requires_the_playhead_on_the_cue() -> None:
    backend, song = _backend()
    song.cues = [_CuePoint("Intro", 0.0), _CuePoint("Drop", 64.0)]
    _move_playhead(backend, 0.0)

    with pytest.raises(CommandError) as error:
        dispatch_command(backend, "locator_delete", {"index": 1})

    assert error.value.code == "INVALID_ARGUMENT"
    assert "transport position set 64.0" in str(error.value.hint)
    assert song.cue_toggle_times == []
    assert [cue.name for cue in song.cues] == ["Intro", "Drop"]


def test_locator_add_rejects_existing_position_and_playing_transport() -> None:
    backend, song = _backend()
    _move_playhead(backend, 16.0)
    dispatch_command(backend, "locator_add", {"time": 16.0})

    with pytest.raises(CommandError):
        dispatch_command(backend, "locator_add", {"time": 16.0})
    _move_playhead(backend, 32.0)
    song.is_playing = True
    with pytest.raises(CommandError):
        dispatch_command(backend, "locator_add", {"time": 32.0})
    with pytest.raises(CommandError):
        dispatch_command(backend, "locator_delete", {"index": 0})
    assert song.cue_toggle_times == [16.0]


def test_transport_position_set_reports_positions_behind_the_song_length() -> None:
    backend, song = _backend()

    with pytest.raises(CommandError) as error:
        _move_playhead(backend, 512.0)

    assert error.value.code == "INVALID_ARGUMENT"
    assert "Songlength" in error.value.message
    assert "song length" in str(error.value.hint)


def test_transport_signature_set_validates_denominator() -> None:
    backend, song = _backend()

    assert dispatch_command(
        backend, "transport_signature_set", {"numerator": 7, "denominator": 8}
    ) == {"numerator": 7, "denominator": 8}
    with pytest.raises(CommandError):
        dispatch_command(backend, "transport_signature_set", {"numerator": 4, "denominator": 3})
    assert (song.signature_numerator, song.signature_denominator) == (7, 8)
