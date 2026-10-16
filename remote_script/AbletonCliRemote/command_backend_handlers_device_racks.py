from __future__ import annotations

from collections.abc import Callable
from typing import Any

from .command_backend_contract import CommandBackend
from .command_backend_validators import (
    _as_bool,
    _as_float,
    _as_int,
    _device_macro_set_args,
    _device_ref_args,
    _invalid_argument,
    _track_index,
)

Handler = Callable[[CommandBackend, dict[str, Any]], dict[str, Any]]


def _handle_device_chains_list(backend: CommandBackend, args: dict[str, Any]) -> dict[str, Any]:
    track_ref, device_ref = _device_ref_args(args)
    track = backend.resolve_track_ref(track_ref)
    device = backend.resolve_device_ref(track, device_ref)
    return backend.device_chains_list(track, device)


def _handle_device_macro_list(backend: CommandBackend, args: dict[str, Any]) -> dict[str, Any]:
    track_ref, device_ref = _device_ref_args(args)
    track = backend.resolve_track_ref(track_ref)
    device = backend.resolve_device_ref(track, device_ref)
    return backend.device_macro_list(track, device)


def _handle_device_macro_set(backend: CommandBackend, args: dict[str, Any]) -> dict[str, Any]:
    track_ref, device_ref, macro_index, value = _device_macro_set_args(args)
    track = backend.resolve_track_ref(track_ref)
    device = backend.resolve_device_ref(track, device_ref)
    return backend.device_macro_set(track, device, macro_index, value)


#: Drum Rack choke groups: 0 = none, 1-16.
_CHOKE_GROUP_MAX = 16


def _resolved_rack(backend: CommandBackend, args: dict[str, Any]) -> tuple[int, Any]:
    track_ref, device_ref = _device_ref_args(args)
    track = backend.resolve_track_ref(track_ref)
    return track, backend.resolve_device_ref(track, device_ref)


def _handle_device_chain_get(backend: CommandBackend, args: dict[str, Any]) -> dict[str, Any]:
    chain_index = _track_index("chain_index", args.get("chain_index"))
    track, device = _resolved_rack(backend, args)
    return backend.device_chain_get(track, device, chain_index)


def _choke_group(raw: Any) -> int:
    parsed = _as_int("choke_group", raw)
    if parsed < 0 or parsed > _CHOKE_GROUP_MAX:
        raise _invalid_argument(
            message=f"choke_group must be between 0 and {_CHOKE_GROUP_MAX}, got {parsed}",
            hint="Use 0 for no choke group or 1-16.",
        )
    return parsed


_CHAIN_SETTING_VALIDATORS: dict[str, Callable[[Any], Any]] = {
    "volume": lambda raw: _as_float("volume", raw),
    "panning": lambda raw: _as_float("panning", raw),
    "mute": lambda raw: _as_bool("mute", raw),
    "solo": lambda raw: _as_bool("solo", raw),
    "choke_group": _choke_group,
}


def _chain_settings(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise _invalid_argument(
            message="settings must be an object",
            hint=f"Pass any of: {', '.join(_CHAIN_SETTING_VALIDATORS)}.",
        )
    unknown = sorted(set(value) - set(_CHAIN_SETTING_VALIDATORS))
    if unknown:
        raise _invalid_argument(
            message=f"unknown chain settings: {', '.join(unknown)}",
            hint=f"Use only: {', '.join(_CHAIN_SETTING_VALIDATORS)}.",
        )
    settings = {
        key: _CHAIN_SETTING_VALIDATORS[key](raw) for key, raw in value.items() if raw is not None
    }
    if not settings:
        raise _invalid_argument(
            message="no chain setting given",
            hint=f"Pass at least one of: {', '.join(_CHAIN_SETTING_VALIDATORS)}.",
        )
    return settings


def _handle_device_chain_set(backend: CommandBackend, args: dict[str, Any]) -> dict[str, Any]:
    chain_index = _track_index("chain_index", args.get("chain_index"))
    settings = _chain_settings(args.get("settings"))
    track, device = _resolved_rack(backend, args)
    return backend.device_chain_set(track, device, chain_index, settings)


def _handle_device_variations_list(backend: CommandBackend, args: dict[str, Any]) -> dict[str, Any]:
    track, device = _resolved_rack(backend, args)
    return backend.device_variations_list(track, device)


def _handle_device_variation_store(backend: CommandBackend, args: dict[str, Any]) -> dict[str, Any]:
    track, device = _resolved_rack(backend, args)
    return backend.device_variation_store(track, device)


def _handle_device_variation_recall(
    backend: CommandBackend, args: dict[str, Any]
) -> dict[str, Any]:
    variation_index = _track_index("variation_index", args.get("variation_index"))
    track, device = _resolved_rack(backend, args)
    return backend.device_variation_recall(track, device, variation_index)


def _handle_device_variation_delete(
    backend: CommandBackend, args: dict[str, Any]
) -> dict[str, Any]:
    variation_index = _track_index("variation_index", args.get("variation_index"))
    track, device = _resolved_rack(backend, args)
    return backend.device_variation_delete(track, device, variation_index)


DEVICE_RACKS_HANDLERS: dict[str, Handler] = {
    "device_chains_list": _handle_device_chains_list,
    "device_macro_list": _handle_device_macro_list,
    "device_macro_set": _handle_device_macro_set,
    "device_chain_get": _handle_device_chain_get,
    "device_chain_set": _handle_device_chain_set,
    "device_variations_list": _handle_device_variations_list,
    "device_variation_store": _handle_device_variation_store,
    "device_variation_recall": _handle_device_variation_recall,
    "device_variation_delete": _handle_device_variation_delete,
}
