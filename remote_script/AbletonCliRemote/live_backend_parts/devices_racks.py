from __future__ import annotations

from typing import Any

from .base import DeviceLocator, _invalid_argument, _not_supported_by_live_api

_MACRO_NAME_PREFIX = "Macro "
#: Chain mixer parameters (DeviceParameter) and plain chain properties that
#: ``device chain set`` changes.
_CHAIN_MIXER_PARAMETERS = ("volume", "panning")
_CHAIN_PROPERTIES = ("mute", "solo", "choke_group")


class LiveBackendDeviceRacksMixin:
    """Rack chain traversal and macro parameter control.

    Split from ``devices.py`` by domain: this module owns Rack-specific
    traversal (chains, drum-rack-adjacent macro parameters), while
    ``devices.py`` owns flat device/parameter listing and standard
    synth/effect helpers.
    """

    def _require_rack_device(self, target_device: Any) -> Any:
        chains = getattr(target_device, "chains", None)
        if not getattr(target_device, "can_have_chains", False):
            raise _invalid_argument(
                message="Device does not support chains (not a Rack device)",
                hint="Target an Instrument/Audio Effect/Drum Rack device.",
            )
        if chains is None:
            raise _not_supported_by_live_api(
                message="Device chains API is not available in Live API",
                hint="Use a Live version exposing device.chains (Live 12+).",
            )
        return chains

    def device_chains_list(self, track: int, device: int | tuple[int, ...]) -> dict[str, Any]:
        target_device = self._ctx._device_at(track, device)
        chains = list(self._require_rack_device(target_device))

        chains_payload = []
        for chain_index, chain in enumerate(chains):
            chain_devices = list(getattr(chain, "devices", []))
            devices_payload = []
            for chain_device_index, chain_device in enumerate(chain_devices):
                chain_path = self._chain_device_path(device, chain_index, chain_device_index)
                stable_ref = self._ctx._device_stable_ref_for(track, chain_path)
                devices_payload.append(
                    {
                        "index": chain_device_index,
                        "name": str(getattr(chain_device, "name", "")),
                        "class_name": str(getattr(chain_device, "class_name", "")),
                        "stable_ref": stable_ref,
                    }
                )
            # Drum Rack chains carry the MIDI note that triggers them; chain order is
            # not the note map. Other rack chains have no note.
            in_note = getattr(chain, "in_note", None)
            chains_payload.append(
                {
                    "index": chain_index,
                    "name": str(getattr(chain, "name", "")),
                    "in_note": int(in_note) if in_note is not None else None,
                    **self._chain_mixer_state(chain),
                    "devices": devices_payload,
                }
            )
        return {"track": track, "device": device, "chains": chains_payload}

    def _chain_mixer_state(self, chain: Any) -> dict[str, Any]:
        volume = chain.mixer_device.volume
        panning = chain.mixer_device.panning
        # Only Drum Rack chains (DrumChain) have a choke group; 0 means none.
        choke_group = getattr(chain, "choke_group", None)
        return {
            "volume": float(volume.value),
            "volume_display": self._ctx._parameter_display_value(volume),
            "panning": float(panning.value),
            "panning_display": self._ctx._parameter_display_value(panning),
            "mute": bool(chain.mute),
            "solo": bool(chain.solo),
            "choke_group": int(choke_group) if choke_group is not None else None,
        }

    def _rack_chain_at(
        self, track: int, device: DeviceLocator, chain_index: int
    ) -> tuple[Any, Any]:
        target_device = self._ctx._device_at(track, device)
        chains = list(self._require_rack_device(target_device))
        if chain_index < 0 or chain_index >= len(chains):
            raise _invalid_argument(
                message=f"chain_index out of range: {chain_index}",
                hint=(
                    f"Use a chain_index in 0..{max(len(chains) - 1, 0)} (see 'device chains list')."
                ),
            )
        return target_device, chains[chain_index]

    def _chain_payload(
        self, track: int, device: DeviceLocator, chain_index: int, chain: Any
    ) -> dict[str, Any]:
        return {
            "track": track,
            "device": device,
            "chain": chain_index,
            "name": str(getattr(chain, "name", "")),
            **self._chain_mixer_state(chain),
        }

    def device_chain_get(
        self, track: int, device: DeviceLocator, chain_index: int
    ) -> dict[str, Any]:
        _rack, chain = self._rack_chain_at(track, device, chain_index)
        return self._chain_payload(track, device, chain_index, chain)

    def device_chain_set(
        self,
        track: int,
        device: DeviceLocator,
        chain_index: int,
        settings: dict[str, Any],
    ) -> dict[str, Any]:
        rack, chain = self._rack_chain_at(track, device, chain_index)
        # Validate every setting before changing anything.
        for key in _CHAIN_MIXER_PARAMETERS:
            if key in settings:
                _require_in_parameter_range(key, getattr(chain.mixer_device, key), settings[key])
        if "choke_group" in settings:
            _require_choke_group_api(rack, chain)

        for key in _CHAIN_MIXER_PARAMETERS:
            if key in settings:
                getattr(chain.mixer_device, key).value = float(settings[key])
        for key in _CHAIN_PROPERTIES:
            if key in settings:
                setattr(chain, key, settings[key])
        return self._chain_payload(track, device, chain_index, chain)

    @staticmethod
    def _chain_device_path(
        device: int | tuple[int, ...], chain_index: int, chain_device_index: int
    ) -> tuple[int, ...]:
        base = (device,) if isinstance(device, int) else tuple(device)
        return (*base, chain_index, chain_device_index)

    def _macro_positions(self, target_device: Any) -> list[int]:
        # Match on original_name: mapped macros on preset racks are usually
        # renamed, but Live keeps original_name at "Macro N".
        parameters = list(getattr(target_device, "parameters", []))
        return [
            index
            for index, parameter in enumerate(parameters)
            if str(
                getattr(parameter, "original_name", None) or getattr(parameter, "name", "")
            ).startswith(_MACRO_NAME_PREFIX)
        ]

    def device_macro_list(self, track: int, device: int | tuple[int, ...]) -> dict[str, Any]:
        target_device = self._ctx._device_at(track, device)
        self._require_rack_device(target_device)
        parameters = list(getattr(target_device, "parameters", []))

        macros_payload = []
        for macro_index, param_index in enumerate(self._macro_positions(target_device)):
            parameter = parameters[param_index]
            stable_ref = (
                self._ctx._parameter_stable_ref(
                    parameter,
                    track_index=track,
                    device_index=device,
                    parameter_index=param_index,
                )
                if isinstance(device, int)
                else self._ctx._stable_ref("parameter", parameter, locator=None)
            )
            macros_payload.append(
                {
                    "index": macro_index,
                    "name": str(getattr(parameter, "name", "")),
                    "value": float(parameter.value),
                    "min": float(getattr(parameter, "min", 0.0)),
                    "max": float(getattr(parameter, "max", 1.0)),
                    "stable_ref": stable_ref,
                }
            )
        return {"track": track, "device": device, "macros": macros_payload}

    def device_macro_set(
        self,
        track: int,
        device: int | tuple[int, ...],
        macro_index: int,
        value: float,
    ) -> dict[str, Any]:
        target_device = self._ctx._device_at(track, device)
        self._require_rack_device(target_device)
        parameters = list(getattr(target_device, "parameters", []))
        macro_positions = self._macro_positions(target_device)

        if macro_index < 0 or macro_index >= len(macro_positions):
            raise _invalid_argument(
                message=f"macro_index out of range: {macro_index}",
                hint=(
                    f"Use a macro_index in 0..{max(len(macro_positions) - 1, 0)} "
                    "(see 'device macro list')."
                ),
            )
        parameter = parameters[macro_positions[macro_index]]
        minimum = float(getattr(parameter, "min", 0.0))
        maximum = float(getattr(parameter, "max", 1.0))
        if value < minimum or value > maximum:
            raise _invalid_argument(
                message=f"value {value} is outside macro range [{minimum}, {maximum}]",
                hint="Use a value within the macro's min/max (see 'device macro list').",
            )
        parameter.value = float(value)
        return {
            "track": track,
            "device": device,
            "macro_index": macro_index,
            "name": str(getattr(parameter, "name", "")),
            "value": float(parameter.value),
        }


def _require_in_parameter_range(name: str, parameter: Any, value: float) -> None:
    minimum = float(parameter.min)
    maximum = float(parameter.max)
    if value < minimum or value > maximum:
        raise _invalid_argument(
            message=f"{name} {value} is outside [{minimum}, {maximum}]",
            hint=f"Pass a {name} within [{minimum}, {maximum}].",
        )


def _require_choke_group_api(rack: Any, chain: Any) -> None:
    if not getattr(rack, "can_have_drum_pads", False):
        raise _invalid_argument(
            message="Choke groups exist only on Drum Rack chains",
            hint="Target a Drum Rack device.",
        )
    if not hasattr(chain, "choke_group"):
        raise _not_supported_by_live_api(
            message="DrumChain.choke_group is not available in Live API",
            hint="Use a Live version exposing DrumChain.choke_group (Live 12+).",
        )
