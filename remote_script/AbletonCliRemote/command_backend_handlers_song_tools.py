from __future__ import annotations

from collections.abc import Callable
from typing import Any

from .command_backend_contract import CommandBackend
from .command_backend_validators import (
    _as_bool,
    _as_float,
    _as_int,
    _device_ref_args,
    _invalid_argument,
    _non_empty_string,
    _non_negative_float,
    _non_negative_int,
    _track_index,
    _track_ref,
)

Handler = Callable[[CommandBackend, dict[str, Any]], dict[str, Any]]

#: Live's color chooser has 70 entries (color_index 0-69).
_COLOR_INDEX_MAX = 69
#: Clip.launch_mode: 0 Trigger, 1 Gate, 2 Toggle, 3 Repeat.
_LAUNCH_MODE_MAX = 3
#: Clip.launch_quantization: 0 Global, 1 None, 2 8 Bars ... 14 1/32.
_LAUNCH_QUANTIZATION_MAX = 14
_SIGNATURE_DENOMINATORS = (1, 2, 4, 8, 16)


def _int_in_range(name: str, value: Any, maximum: int, minimum: int = 0) -> int:
    parsed = _as_int(name, value)
    if parsed < minimum or parsed > maximum:
        raise _invalid_argument(
            message=f"{name} must be between {minimum} and {maximum}, got {parsed}",
            hint=f"Pass an integer from {minimum} to {maximum} for '{name}'.",
        )
    return parsed


def _resolved_device(backend: CommandBackend, args: dict[str, Any]) -> tuple[int, Any]:
    track_ref, device_ref = _device_ref_args(args)
    track = backend.resolve_track_ref(track_ref)
    return track, backend.resolve_device_ref(track, device_ref)


def _handle_device_delete(backend: CommandBackend, args: dict[str, Any]) -> dict[str, Any]:
    track, device = _resolved_device(backend, args)
    return backend.device_delete(track, device)


def _handle_device_move(backend: CommandBackend, args: dict[str, Any]) -> dict[str, Any]:
    to_index = _non_negative_int("to_index", args.get("to_index"))
    track, device = _resolved_device(backend, args)
    return backend.device_move(track, device, to_index)


def _handle_device_insert(backend: CommandBackend, args: dict[str, Any]) -> dict[str, Any]:
    device_name = _non_empty_string("device_name", args.get("device_name"))
    raw_index = args.get("index")
    index = None if raw_index is None else _non_negative_int("index", raw_index)
    track = backend.resolve_track_ref(_track_ref(args.get("track_ref")))
    return backend.device_insert(track, device_name, index)


def _handle_device_enabled_set(backend: CommandBackend, args: dict[str, Any]) -> dict[str, Any]:
    value = _as_bool("value", args.get("value"))
    track, device = _resolved_device(backend, args)
    return backend.device_enabled_set(track, device, value)


def _handle_device_parameters_list(backend: CommandBackend, args: dict[str, Any]) -> dict[str, Any]:
    track, device = _resolved_device(backend, args)
    return backend.device_parameters_list(track, device)


def _handle_track_color_set(backend: CommandBackend, args: dict[str, Any]) -> dict[str, Any]:
    track = backend.resolve_track_ref(_track_ref(args.get("track_ref")))
    color_index = _int_in_range("color_index", args.get("color_index"), _COLOR_INDEX_MAX)
    return backend.track_color_set(track, color_index)


def _handle_clip_color_set(backend: CommandBackend, args: dict[str, Any]) -> dict[str, Any]:
    track = _track_index("track", args.get("track"))
    clip = _track_index("clip", args.get("clip"))
    color_index = _int_in_range("color_index", args.get("color_index"), _COLOR_INDEX_MAX)
    return backend.clip_color_set(track, clip, color_index)


def _handle_clip_launch_get(backend: CommandBackend, args: dict[str, Any]) -> dict[str, Any]:
    track = _track_index("track", args.get("track"))
    clip = _track_index("clip", args.get("clip"))
    return backend.clip_launch_get(track, clip)


def _launch_settings(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise _invalid_argument(
            message="settings must be an object",
            hint="Pass launch_mode, launch_quantization, legato and/or velocity_amount.",
        )
    validators: dict[str, Callable[[Any], Any]] = {
        "launch_mode": lambda raw: _int_in_range("launch_mode", raw, _LAUNCH_MODE_MAX),
        "launch_quantization": lambda raw: _int_in_range(
            "launch_quantization", raw, _LAUNCH_QUANTIZATION_MAX
        ),
        "legato": lambda raw: _as_bool("legato", raw),
        "velocity_amount": lambda raw: _unit_float("velocity_amount", raw),
    }
    unknown = sorted(set(value) - set(validators))
    if unknown:
        raise _invalid_argument(
            message=f"unknown launch settings: {', '.join(unknown)}",
            hint=f"Use only: {', '.join(validators)}.",
        )
    settings = {key: validators[key](raw) for key, raw in value.items() if raw is not None}
    if not settings:
        raise _invalid_argument(
            message="no launch setting given",
            hint="Pass at least one of: launch_mode, launch_quantization, legato, velocity_amount.",
        )
    return settings


def _unit_float(name: str, value: Any) -> float:
    parsed = _as_float(name, value)
    if parsed < 0.0 or parsed > 1.0:
        raise _invalid_argument(
            message=f"{name} must be between 0.0 and 1.0, got {parsed}",
            hint=f"Pass a value from 0.0 to 1.0 for '{name}'.",
        )
    return parsed


def _handle_clip_launch_set(backend: CommandBackend, args: dict[str, Any]) -> dict[str, Any]:
    track = _track_index("track", args.get("track"))
    clip = _track_index("clip", args.get("clip"))
    settings = _launch_settings(args.get("settings"))
    return backend.clip_launch_set(track, clip, settings)


def _handle_tracks_duplicate(backend: CommandBackend, args: dict[str, Any]) -> dict[str, Any]:
    return backend.tracks_duplicate(_track_index("track", args.get("track")))


def _handle_scenes_duplicate(backend: CommandBackend, args: dict[str, Any]) -> dict[str, Any]:
    return backend.scenes_duplicate(_track_index("scene", args.get("scene")))


def _handle_scenes_delete(backend: CommandBackend, args: dict[str, Any]) -> dict[str, Any]:
    return backend.scenes_delete(_track_index("scene", args.get("scene")))


def _handle_return_tracks_create(backend: CommandBackend, _args: dict[str, Any]) -> dict[str, Any]:
    return backend.return_tracks_create()


def _handle_return_tracks_delete(backend: CommandBackend, args: dict[str, Any]) -> dict[str, Any]:
    return backend.return_tracks_delete(_track_index("index", args.get("index")))


def _handle_locators_list(backend: CommandBackend, _args: dict[str, Any]) -> dict[str, Any]:
    return backend.locators_list()


def _handle_locator_add(backend: CommandBackend, args: dict[str, Any]) -> dict[str, Any]:
    time = _non_negative_float("time", args.get("time"))
    raw_name = args.get("name")
    name = None if raw_name is None else _non_empty_string("name", raw_name)
    return backend.locator_add(time, name)


def _handle_locator_delete(backend: CommandBackend, args: dict[str, Any]) -> dict[str, Any]:
    return backend.locator_delete(_track_index("index", args.get("index")))


def _time_signature(args: dict[str, Any]) -> tuple[int, int]:
    numerator = _int_in_range("numerator", args.get("numerator"), 99, minimum=1)
    denominator = _as_int("denominator", args.get("denominator"))
    if denominator not in _SIGNATURE_DENOMINATORS:
        raise _invalid_argument(
            message=f"denominator must be one of {_SIGNATURE_DENOMINATORS}, got {denominator}",
            hint="Use 1, 2, 4, 8 or 16.",
        )
    return numerator, denominator


def _handle_transport_signature_set(
    backend: CommandBackend, args: dict[str, Any]
) -> dict[str, Any]:
    return backend.transport_signature_set(*_time_signature(args))


def _track_and_clip(args: dict[str, Any]) -> tuple[int, int]:
    return _track_index("track", args.get("track")), _track_index("clip", args.get("clip"))


def _handle_clip_crop(backend: CommandBackend, args: dict[str, Any]) -> dict[str, Any]:
    return backend.clip_crop(*_track_and_clip(args))


def _handle_clip_duplicate_loop(backend: CommandBackend, args: dict[str, Any]) -> dict[str, Any]:
    return backend.clip_duplicate_loop(*_track_and_clip(args))


def _handle_clip_signature_set(backend: CommandBackend, args: dict[str, Any]) -> dict[str, Any]:
    track, clip = _track_and_clip(args)
    return backend.clip_signature_set(track, clip, *_time_signature(args))


SONG_TOOLS_HANDLERS: dict[str, Handler] = {
    "device_delete": _handle_device_delete,
    "device_move": _handle_device_move,
    "device_insert": _handle_device_insert,
    "device_enabled_set": _handle_device_enabled_set,
    "device_parameters_list": _handle_device_parameters_list,
    "track_color_set": _handle_track_color_set,
    "clip_color_set": _handle_clip_color_set,
    "clip_launch_get": _handle_clip_launch_get,
    "clip_launch_set": _handle_clip_launch_set,
    "tracks_duplicate": _handle_tracks_duplicate,
    "scenes_duplicate": _handle_scenes_duplicate,
    "scenes_delete": _handle_scenes_delete,
    "return_tracks_create": _handle_return_tracks_create,
    "return_tracks_delete": _handle_return_tracks_delete,
    "locators_list": _handle_locators_list,
    "locator_add": _handle_locator_add,
    "locator_delete": _handle_locator_delete,
    "transport_signature_set": _handle_transport_signature_set,
    "clip_crop": _handle_clip_crop,
    "clip_duplicate_loop": _handle_clip_duplicate_loop,
    "clip_signature_set": _handle_clip_signature_set,
}
