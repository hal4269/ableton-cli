from __future__ import annotations

from typing import Any

from .base import DeviceLocator, _invalid_argument, _not_supported_by_live_api
from .devices import _value_for_display

_DEVICE_ON_PARAMETER = "Device On"


class LiveBackendDeviceEditMixin:
    """Editing the device chain of a track: delete, move, on/off, parameter listing.

    Device locators are flat indexes or chain-nested paths, so every command here
    also reaches devices inside rack chains (via a stable_ref from
    ``device chains list``), except ``device_move``, which moves top-level devices.
    """

    def _device_container(self, track: int, device: DeviceLocator) -> tuple[Any, int]:
        """Return the object holding the device (track or rack chain) and its index there."""
        self._ctx._device_at(track, device)
        if isinstance(device, int):
            return self._ctx._track_at(track), device
        *rack_path, chain_index, device_index = device
        rack_locator: DeviceLocator = rack_path[0] if len(rack_path) == 1 else tuple(rack_path)
        rack = self._ctx._device_at(track, rack_locator)
        return list(rack.chains)[chain_index], device_index

    def device_delete(self, track: int, device: DeviceLocator) -> dict[str, Any]:
        container, index = self._device_container(track, device)
        delete_device = getattr(container, "delete_device", None)
        if not callable(delete_device):
            raise _not_supported_by_live_api(
                message="delete_device is not available in Live API",
                hint="Use a Live version exposing track.delete_device (Live 12+).",
            )
        delete_device(index)
        return {
            "track": track,
            "device": device,
            "deleted": True,
            "device_count": len(list(getattr(container, "devices", []))),
        }

    def device_move(self, track: int, device: DeviceLocator, to_index: int) -> dict[str, Any]:
        if not isinstance(device, int):
            raise _invalid_argument(
                message="device move supports top-level track devices only",
                hint="Select the device with --device-index, --device-name or --device-query.",
            )
        target_track = self._ctx._track_at(track)
        devices = list(target_track.devices)
        target_device = self._ctx._device_at(track, device)
        if to_index < 0 or to_index >= len(devices):
            raise _invalid_argument(
                message=f"destination device index out of range: {to_index}",
                hint="Use a destination index from 'track info'.",
            )
        move_device = getattr(self._ctx._song(), "move_device", None)
        if not callable(move_device):
            raise _not_supported_by_live_api(
                message="Song.move_device is not available in Live API",
                hint="Use a Live version exposing song.move_device (Live 12+).",
            )
        # Live picks the nearest valid position (instruments stay first) and returns it.
        inserted = move_device(target_device, target_track, to_index)
        return {"track": track, "device": device, "to_index": int(inserted)}

    def device_enabled_set(self, track: int, device: DeviceLocator, value: bool) -> dict[str, Any]:
        target_device = self._ctx._device_at(track, device)
        for parameter in list(getattr(target_device, "parameters", [])):
            name = getattr(parameter, "original_name", None) or getattr(parameter, "name", "")
            if str(name) == _DEVICE_ON_PARAMETER:
                parameter.value = 1.0 if value else 0.0
                return {"track": track, "device": device, "enabled": bool(parameter.value)}
        raise _invalid_argument(
            message=f"Device has no '{_DEVICE_ON_PARAMETER}' parameter",
            hint="Target a device with an on/off switch.",
        )

    def device_parameters_list(self, track: int, device: DeviceLocator) -> dict[str, Any]:
        target_device = self._ctx._device_at(track, device)
        flat_index = device if isinstance(device, int) else None
        parameters = [
            self._ctx._serialize_parameter(
                parameter,
                index,
                track_index=track if flat_index is not None else None,
                device_index=flat_index,
            )
            for index, parameter in enumerate(list(getattr(target_device, "parameters", [])))
        ]
        return {
            "track": track,
            "device": device,
            "device_name": str(getattr(target_device, "name", "")),
            "class_name": str(getattr(target_device, "class_name", "")),
            "parameter_count": len(parameters),
            "parameters": parameters,
        }

    def device_insert(self, track: int, device_name: str, index: int | None) -> dict[str, Any]:
        target_track = self._ctx._track_at(track)
        target_index = self._insert_native_device(target_track, device_name, index)
        return {
            "track": track,
            "device_name": device_name,
            "index": target_index,
            "devices": self._device_summaries(target_track),
        }

    @staticmethod
    def _insert_native_device(target_track: Any, device_name: str, index: int | None) -> int:
        insert_device = getattr(target_track, "insert_device", None)
        if not callable(insert_device):
            raise _not_supported_by_live_api(
                message="Track.insert_device is not available in Live API",
                hint="Use Live 12.1.10+ (Track.insert_device), or 'browser load' to append.",
            )
        device_count = len(list(target_track.devices))
        target_index = device_count if index is None else index
        if target_index > device_count:
            raise _invalid_argument(
                message=f"insert index out of range: {target_index}",
                hint=f"Use an index in 0..{device_count} (omit it to append).",
            )
        try:
            insert_device(device_name, target_index)
        except (RuntimeError, ValueError) as error:
            raise _invalid_argument(
                message=f"Live could not insert device {device_name!r}: {error}",
                hint="Use a native Live device name as shown in the browser (e.g. 'EQ Eight').",
            ) from error
        return target_index

    @staticmethod
    def _device_summaries(target_track: Any) -> list[dict[str, Any]]:
        return [
            {
                "index": position,
                "name": str(getattr(device, "name", "")),
                "class_name": str(getattr(device, "class_name", "")),
            }
            for position, device in enumerate(list(target_track.devices))
        ]

    def _return_track_device_at(self, return_track: int, device: int) -> Any:
        devices = list(self._ctx._return_track_at(return_track).devices)
        if device >= len(devices):
            raise _invalid_argument(
                message=f"device out of range: {device}",
                hint="Use a valid device index from 'return-track device list'.",
            )
        return devices[device]

    def return_track_name_set(self, return_track: int, name: str) -> dict[str, Any]:
        target = self._ctx._return_track_at(return_track)
        target.name = name
        return {"return_track": return_track, "name": str(target.name)}

    def return_track_devices_list(self, return_track: int) -> dict[str, Any]:
        target = self._ctx._return_track_at(return_track)
        return {"return_track": return_track, "devices": self._device_summaries(target)}

    def return_track_device_insert(
        self, return_track: int, device_name: str, index: int | None
    ) -> dict[str, Any]:
        target = self._ctx._return_track_at(return_track)
        target_index = self._insert_native_device(target, device_name, index)
        return {
            "return_track": return_track,
            "device_name": device_name,
            "index": target_index,
            "devices": self._device_summaries(target),
        }

    def return_track_device_parameters_list(self, return_track: int, device: int) -> dict[str, Any]:
        target_device = self._return_track_device_at(return_track, device)
        parameters = []
        for position, parameter in enumerate(list(target_device.parameters)):
            quantized = bool(getattr(parameter, "is_quantized", False))
            parameters.append(
                {
                    "index": position,
                    "name": str(getattr(parameter, "name", "")),
                    "value": float(parameter.value),
                    "min": self._ctx._safe_float(getattr(parameter, "min", None)),
                    "max": self._ctx._safe_float(getattr(parameter, "max", None)),
                    "is_quantized": quantized,
                    "value_items": list(getattr(parameter, "value_items", ())) if quantized else [],
                    "display_value": self._ctx._parameter_display_value(parameter),
                }
            )
        return {
            "return_track": return_track,
            "device": device,
            "device_name": str(getattr(target_device, "name", "")),
            "class_name": str(getattr(target_device, "class_name", "")),
            "parameters": parameters,
        }

    def return_track_device_parameter_set_display(
        self, return_track: int, device: int, parameter: str, display: str
    ) -> dict[str, Any]:
        target_device = self._return_track_device_at(return_track, device)
        parameters = list(target_device.parameters)
        matches = [i for i, p in enumerate(parameters) if str(getattr(p, "name", "")) == parameter]
        if not matches:
            raise _invalid_argument(
                message=f"parameter not found: {parameter}",
                hint="Use an exact parameter name from 'return-track device parameters'.",
            )
        target_parameter = parameters[matches[0]]
        target_parameter.value = _value_for_display(target_parameter, display)
        return {
            "return_track": return_track,
            "device": device,
            "parameter": matches[0],
            "value": float(target_parameter.value),
            "display_value": self._ctx._parameter_display_value(target_parameter),
        }
