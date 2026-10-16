"""Song settings, scene tempo/signature, track monitoring/folding and view control
(Live 12+ Live Object Model)."""

from __future__ import annotations

from typing import Any

from ..live_api import recording_quantization_value
from ..song_settings_specs import (
    CAPTURE_DESTINATIONS,
    LIVE_VIEW_NAMES,
    MONITORING_STATES,
    RECORD_QUANTIZATION_NAMES,
    ROOT_NOTE_NAMES,
)
from .base import _invalid_argument


def _loop_payload(song: Any) -> dict[str, Any]:
    start = float(song.loop_start)
    length = float(song.loop_length)
    return {"enabled": bool(song.loop), "start": start, "length": length, "end": start + length}


def _scale_payload(song: Any) -> dict[str, Any]:
    root_note = int(song.root_note)
    return {
        "root_note": root_note,
        "root_name": ROOT_NOTE_NAMES[root_note],
        "name": str(song.scale_name),
        "mode": bool(song.scale_mode),
        "intervals": [int(interval) for interval in song.scale_intervals],
    }


def _record_quantization_name(song: Any) -> str:
    return RECORD_QUANTIZATION_NAMES[int(song.midi_recording_quantization)]


def song_settings_payload(song: Any) -> dict[str, Any]:
    """Readable song settings, merged into ``song info``."""
    return {
        "back_to_arranger": bool(song.back_to_arranger),
        "loop": _loop_payload(song),
        "metronome": bool(song.metronome),
        "swing_amount": float(song.swing_amount),
        "groove_amount": float(song.groove_amount),
        "scale": _scale_payload(song),
        "midi_recording_quantization": _record_quantization_name(song),
        "can_capture_midi": bool(song.can_capture_midi),
    }


def scene_settings_payload(scene: Any) -> dict[str, Any]:
    """Scene tempo and time signature, None when the scene does not set them."""
    signature = None
    if bool(scene.time_signature_enabled):
        signature = {
            "numerator": int(scene.time_signature_numerator),
            "denominator": int(scene.time_signature_denominator),
        }
    return {
        "tempo": float(scene.tempo) if bool(scene.tempo_enabled) else None,
        "signature": signature,
    }


def track_group_payload(song: Any, track: Any, same_object: Any) -> dict[str, Any]:
    """Group state of a track: foldable (group) tracks and group membership."""
    is_foldable = bool(track.is_foldable)
    group_index = None
    if bool(track.is_grouped):
        group = track.group_track
        group_index = next(
            index for index, candidate in enumerate(song.tracks) if same_object(candidate, group)
        )
    return {
        "is_foldable": is_foldable,
        "fold_state": bool(track.fold_state) if is_foldable else None,
        "is_grouped": bool(track.is_grouped),
        "group_track": group_index,
    }


class LiveBackendSongSettingsMixin:
    """Back to Arrangement, loop region, metronome, swing/groove, key and scale,
    MIDI record quantization and Capture MIDI."""

    def back_to_arranger(self) -> dict[str, Any]:
        song = self._ctx._song()
        # The button is lit (True) while the Session overrides the Arrangement;
        # setting it to False is what clicking "Back to Arrangement" does.
        song.back_to_arranger = False
        return {"back_to_arranger": bool(song.back_to_arranger)}

    def song_loop_get(self) -> dict[str, Any]:
        return _loop_payload(self._ctx._song())

    def song_loop_set(self, settings: dict[str, Any]) -> dict[str, Any]:
        song = self._ctx._song()
        if "start" in settings:
            song.loop_start = settings["start"]
        if "length" in settings:
            song.loop_length = settings["length"]
        if "enabled" in settings:
            song.loop = settings["enabled"]
        return _loop_payload(song)

    def song_metronome_set(self, value: bool) -> dict[str, Any]:
        song = self._ctx._song()
        song.metronome = value
        return {"metronome": bool(song.metronome)}

    def song_swing_set(self, value: float) -> dict[str, Any]:
        song = self._ctx._song()
        song.swing_amount = value
        return {"swing_amount": float(song.swing_amount)}

    def song_groove_amount_set(self, value: float) -> dict[str, Any]:
        song = self._ctx._song()
        song.groove_amount = value
        return {"groove_amount": float(song.groove_amount)}

    def song_scale_set(self, settings: dict[str, Any]) -> dict[str, Any]:
        song = self._ctx._song()
        if "root_note" in settings:
            song.root_note = settings["root_note"]
        if "name" in settings:
            song.scale_name = settings["name"]
        if "mode" in settings:
            song.scale_mode = settings["mode"]
        return _scale_payload(song)

    def song_record_quantization_set(self, value: str) -> dict[str, Any]:
        song = self._ctx._song()
        index = RECORD_QUANTIZATION_NAMES.index(value)
        song.midi_recording_quantization = recording_quantization_value(index)
        return {"midi_recording_quantization": _record_quantization_name(song)}

    def song_capture_midi(self, destination: str) -> dict[str, Any]:
        song = self._ctx._song()
        if not bool(song.can_capture_midi):
            raise _invalid_argument(
                message="Live has no recently played MIDI to capture",
                hint="Play some MIDI into an armed or monitoring track first.",
            )
        song.capture_midi(CAPTURE_DESTINATIONS.index(destination))
        return {"captured": True, "destination": destination}


class LiveBackendSceneSettingsMixin:
    """Per-scene tempo and time signature (Live 12+)."""

    def scene_tempo_set(self, scene: int, bpm: float | None) -> dict[str, Any]:
        target = self._ctx._scene_at(scene)
        if bpm is None:
            target.tempo_enabled = False
        else:
            target.tempo = bpm
            target.tempo_enabled = True
        return {"scene": scene, "tempo": scene_settings_payload(target)["tempo"]}

    def scene_signature_set(
        self, scene: int, numerator: int | None, denominator: int | None
    ) -> dict[str, Any]:
        target = self._ctx._scene_at(scene)
        if numerator is None or denominator is None:
            target.time_signature_enabled = False
        else:
            target.time_signature_numerator = numerator
            target.time_signature_denominator = denominator
            target.time_signature_enabled = True
        return {"scene": scene, "signature": scene_settings_payload(target)["signature"]}


class LiveBackendTrackStateMixin:
    """Track monitoring and group folding."""

    def _monitorable_track(self, track: int) -> Any:
        target = self._ctx._track_at(track)
        if bool(target.is_foldable):
            raise _invalid_argument(
                message=f"track {track} is a group track and has no monitoring state",
                hint="Use an audio or MIDI track; group, return and master tracks have no monitor.",
            )
        return target

    def track_monitoring_get(self, track: int) -> dict[str, Any]:
        target = self._monitorable_track(track)
        return {
            "track": track,
            "monitoring": MONITORING_STATES[int(target.current_monitoring_state)],
        }

    def track_monitoring_set(self, track: int, value: str) -> dict[str, Any]:
        target = self._monitorable_track(track)
        target.current_monitoring_state = MONITORING_STATES.index(value)
        return self.track_monitoring_get(track)

    def track_fold_set(self, track: int, value: bool) -> dict[str, Any]:
        target = self._ctx._track_at(track)
        if not bool(target.is_foldable):
            raise _invalid_argument(
                message=f"track {track} is not a group track and cannot be folded",
                hint="Pick a track with is_foldable=true from 'tracks list'.",
            )
        target.fold_state = 1 if value else 0
        return {"track": track, "fold_state": bool(target.fold_state)}


class LiveBackendViewMixin:
    """Showing Live's views and selecting tracks, scenes and clip slots."""

    def view_show(self, view: str) -> dict[str, Any]:
        live_view = LIVE_VIEW_NAMES[view]
        app_view = self._ctx._application().view
        app_view.focus_view(live_view)
        return {
            "view": view,
            "live_view": live_view,
            "visible": bool(app_view.is_view_visible(live_view)),
        }

    def view_select_track(self, track: int) -> dict[str, Any]:
        target = self._ctx._track_at(track)
        self._ctx._song().view.selected_track = target
        return {"track": track, "name": str(target.name)}

    def view_select_scene(self, scene: int) -> dict[str, Any]:
        target = self._ctx._scene_at(scene)
        self._ctx._song().view.selected_scene = target
        return {"scene": scene, "name": str(target.name)}

    def view_select_clip(self, track: int, clip: int) -> dict[str, Any]:
        slot = self._ctx._clip_slot_at(track, clip)
        song_view = self._ctx._song().view
        song_view.highlighted_clip_slot = slot
        has_clip = bool(slot.has_clip)
        if has_clip:
            song_view.detail_clip = slot.clip
        return {"track": track, "clip": clip, "has_clip": has_clip}
