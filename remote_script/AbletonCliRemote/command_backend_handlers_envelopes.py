from __future__ import annotations

from collections.abc import Callable
from typing import Any

from .command_backend_contract import CommandBackend
from .command_backend_validators import _clip_envelope_clear_args, _clip_envelope_set_args

Handler = Callable[[CommandBackend, dict[str, Any]], dict[str, Any]]


def _resolved_parameter(
    backend: CommandBackend,
    track: int,
    device_target: tuple[dict[str, Any], dict[str, Any]],
) -> tuple[int | tuple[int, ...], int]:
    device_ref, parameter_ref = device_target
    device = backend.resolve_device_ref(track, device_ref)
    return device, backend.resolve_parameter_ref(track, device, parameter_ref)


def _handle_clip_envelope_set(backend: CommandBackend, args: dict[str, Any]) -> dict[str, Any]:
    track, clip, device_target, mixer_target, points, mode = _clip_envelope_set_args(args)
    if mixer_target is not None:
        mixer, send_index = mixer_target
        return backend.clip_mixer_envelope_set(track, clip, mixer, send_index, points, mode)
    assert device_target is not None
    device, parameter = _resolved_parameter(backend, track, device_target)
    return backend.clip_envelope_set(track, clip, device, parameter, points, mode)


def _handle_clip_envelope_clear(backend: CommandBackend, args: dict[str, Any]) -> dict[str, Any]:
    track, clip, device_target, mixer_target, clear_all = _clip_envelope_clear_args(args)
    if clear_all:
        return backend.clip_envelope_clear(track, clip, None, None, True)
    if mixer_target is not None:
        mixer, send_index = mixer_target
        return backend.clip_mixer_envelope_clear(track, clip, mixer, send_index)
    assert device_target is not None
    device, parameter = _resolved_parameter(backend, track, device_target)
    return backend.clip_envelope_clear(track, clip, device, parameter, False)


ENVELOPE_HANDLERS: dict[str, Handler] = {
    "clip_envelope_set": _handle_clip_envelope_set,
    "clip_envelope_clear": _handle_clip_envelope_clear,
}
