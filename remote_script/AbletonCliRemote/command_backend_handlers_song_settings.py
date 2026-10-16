from __future__ import annotations

from collections.abc import Callable
from typing import Any

from .command_backend_contract import CommandBackend
from .command_backend_validators import (
    _as_bool,
    _as_float,
    _as_int,
    _bounded_float,
    _invalid_argument,
    _non_empty_string,
    _non_negative_float,
    _tempo,
    _track_index,
    _track_ref,
)
from .song_settings_specs import (
    CAPTURE_DESTINATIONS,
    GROOVE_AMOUNT_MAX,
    LIVE_VIEW_NAMES,
    MONITORING_STATES,
    RECORD_QUANTIZATION_NAMES,
    ROOT_NOTE_NAMES,
    SWING_AMOUNT_MAX,
)

Handler = Callable[[CommandBackend, dict[str, Any]], dict[str, Any]]

_SIGNATURE_DENOMINATORS = (1, 2, 4, 8, 16)
_SIGNATURE_NUMERATOR_MAX = 99


def _choice(name: str, value: Any, choices: tuple[str, ...] | list[str]) -> str:
    if not isinstance(value, str) or value not in choices:
        raise _invalid_argument(
            message=f"{name} must be one of {', '.join(choices)}, got {value!r}",
            hint=f"Pass one of: {', '.join(choices)}.",
        )
    return value


def _settings(value: Any, validators: dict[str, Callable[[Any], Any]], what: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise _invalid_argument(
            message="settings must be an object",
            hint=f"Pass {what} settings: {', '.join(validators)}.",
        )
    unknown = sorted(set(value) - set(validators))
    if unknown:
        raise _invalid_argument(
            message=f"unknown {what} settings: {', '.join(unknown)}",
            hint=f"Use only: {', '.join(validators)}.",
        )
    settings = {key: validators[key](raw) for key, raw in value.items() if raw is not None}
    if not settings:
        raise _invalid_argument(
            message=f"no {what} setting given",
            hint=f"Pass at least one of: {', '.join(validators)}.",
        )
    return settings


def _positive_float(name: str, value: Any) -> float:
    parsed = _as_float(name, value)
    if parsed <= 0.0:
        raise _invalid_argument(
            message=f"{name} must be > 0, got {parsed}",
            hint=f"Pass a positive number of beats for '{name}'.",
        )
    return parsed


def _root_note(value: Any) -> int:
    parsed = _as_int("root_note", value)
    if parsed < 0 or parsed >= len(ROOT_NOTE_NAMES):
        raise _invalid_argument(
            message=f"root_note must be between 0 and 11, got {parsed}",
            hint="Use 0 for C up to 11 for B.",
        )
    return parsed


def _handle_back_to_arranger(backend: CommandBackend, _args: dict[str, Any]) -> dict[str, Any]:
    return backend.back_to_arranger()


def _handle_song_loop_get(backend: CommandBackend, _args: dict[str, Any]) -> dict[str, Any]:
    return backend.song_loop_get()


def _handle_song_loop_set(backend: CommandBackend, args: dict[str, Any]) -> dict[str, Any]:
    settings = _settings(
        args.get("settings"),
        {
            "enabled": lambda raw: _as_bool("enabled", raw),
            "start": lambda raw: _non_negative_float("start", raw),
            "length": lambda raw: _positive_float("length", raw),
        },
        "loop",
    )
    return backend.song_loop_set(settings)


def _handle_song_metronome_set(backend: CommandBackend, args: dict[str, Any]) -> dict[str, Any]:
    return backend.song_metronome_set(_as_bool("value", args.get("value")))


def _handle_song_swing_set(backend: CommandBackend, args: dict[str, Any]) -> dict[str, Any]:
    value = _bounded_float(
        name="value",
        value=args.get("value"),
        minimum=0.0,
        maximum=SWING_AMOUNT_MAX,
        hint="Use a swing amount from 0.0 to 1.0.",
    )
    return backend.song_swing_set(value)


def _handle_song_groove_amount_set(backend: CommandBackend, args: dict[str, Any]) -> dict[str, Any]:
    value = _bounded_float(
        name="value",
        value=args.get("value"),
        minimum=0.0,
        maximum=GROOVE_AMOUNT_MAX,
        hint=f"Use a groove amount from 0.0 to {GROOVE_AMOUNT_MAX} (0-130%).",
    )
    return backend.song_groove_amount_set(value)


def _handle_song_scale_set(backend: CommandBackend, args: dict[str, Any]) -> dict[str, Any]:
    settings = _settings(
        args.get("settings"),
        {
            "root_note": _root_note,
            "name": lambda raw: _non_empty_string("name", raw),
            "mode": lambda raw: _as_bool("mode", raw),
        },
        "scale",
    )
    return backend.song_scale_set(settings)


def _handle_song_record_quantization_set(
    backend: CommandBackend, args: dict[str, Any]
) -> dict[str, Any]:
    value = _choice("value", args.get("value"), RECORD_QUANTIZATION_NAMES)
    return backend.song_record_quantization_set(value)


def _handle_song_capture_midi(backend: CommandBackend, args: dict[str, Any]) -> dict[str, Any]:
    destination = _choice("destination", args.get("destination"), CAPTURE_DESTINATIONS)
    return backend.song_capture_midi(destination)


def _handle_scene_tempo_set(backend: CommandBackend, args: dict[str, Any]) -> dict[str, Any]:
    scene = _track_index("scene", args.get("scene"))
    raw_bpm = args.get("bpm")
    bpm = None if raw_bpm is None else _tempo(raw_bpm)
    return backend.scene_tempo_set(scene, bpm)


def _handle_scene_signature_set(backend: CommandBackend, args: dict[str, Any]) -> dict[str, Any]:
    scene = _track_index("scene", args.get("scene"))
    raw_numerator = args.get("numerator")
    raw_denominator = args.get("denominator")
    if raw_numerator is None and raw_denominator is None:
        return backend.scene_signature_set(scene, None, None)
    if raw_numerator is None or raw_denominator is None:
        raise _invalid_argument(
            message="numerator and denominator must be given together",
            hint="Pass both (e.g. 7 and 8), or neither to clear the scene's signature.",
        )
    numerator = _as_int("numerator", raw_numerator)
    denominator = _as_int("denominator", raw_denominator)
    if not 1 <= numerator <= _SIGNATURE_NUMERATOR_MAX or denominator not in _SIGNATURE_DENOMINATORS:
        raise _invalid_argument(
            message=f"invalid time signature {numerator}/{denominator}",
            hint="Use a numerator 1-99 and a denominator of 1, 2, 4, 8 or 16.",
        )
    return backend.scene_signature_set(scene, numerator, denominator)


def _resolved_track(backend: CommandBackend, args: dict[str, Any]) -> int:
    return backend.resolve_track_ref(_track_ref(args.get("track_ref")))


def _handle_track_monitoring_get(backend: CommandBackend, args: dict[str, Any]) -> dict[str, Any]:
    return backend.track_monitoring_get(_resolved_track(backend, args))


def _handle_track_monitoring_set(backend: CommandBackend, args: dict[str, Any]) -> dict[str, Any]:
    value = _choice("value", args.get("value"), MONITORING_STATES)
    return backend.track_monitoring_set(_resolved_track(backend, args), value)


def _handle_track_fold_set(backend: CommandBackend, args: dict[str, Any]) -> dict[str, Any]:
    value = _as_bool("value", args.get("value"))
    return backend.track_fold_set(_resolved_track(backend, args), value)


def _handle_view_show(backend: CommandBackend, args: dict[str, Any]) -> dict[str, Any]:
    return backend.view_show(_choice("view", args.get("view"), list(LIVE_VIEW_NAMES)))


def _handle_view_select_track(backend: CommandBackend, args: dict[str, Any]) -> dict[str, Any]:
    return backend.view_select_track(_track_index("track", args.get("track")))


def _handle_view_select_scene(backend: CommandBackend, args: dict[str, Any]) -> dict[str, Any]:
    return backend.view_select_scene(_track_index("scene", args.get("scene")))


def _handle_view_select_clip(backend: CommandBackend, args: dict[str, Any]) -> dict[str, Any]:
    track = _track_index("track", args.get("track"))
    clip = _track_index("clip", args.get("clip"))
    return backend.view_select_clip(track, clip)


SONG_SETTINGS_HANDLERS: dict[str, Handler] = {
    "back_to_arranger": _handle_back_to_arranger,
    "song_loop_get": _handle_song_loop_get,
    "song_loop_set": _handle_song_loop_set,
    "song_metronome_set": _handle_song_metronome_set,
    "song_swing_set": _handle_song_swing_set,
    "song_groove_amount_set": _handle_song_groove_amount_set,
    "song_scale_set": _handle_song_scale_set,
    "song_record_quantization_set": _handle_song_record_quantization_set,
    "song_capture_midi": _handle_song_capture_midi,
    "scene_tempo_set": _handle_scene_tempo_set,
    "scene_signature_set": _handle_scene_signature_set,
    "track_monitoring_get": _handle_track_monitoring_get,
    "track_monitoring_set": _handle_track_monitoring_set,
    "track_fold_set": _handle_track_fold_set,
    "view_show": _handle_view_show,
    "view_select_track": _handle_view_select_track,
    "view_select_scene": _handle_view_select_scene,
    "view_select_clip": _handle_view_select_clip,
}
