from __future__ import annotations

from typing import Any

from .base import DeviceLocator, _invalid_argument, _not_supported_by_live_api


class LiveBackendRackVariationsMixin:
    """Rack macro variations (RackDevice.variation_count, store/recall/delete).

    Live works on the selected variation, so recall and delete select the
    requested index first. Mixed into the rack service next to
    ``LiveBackendDeviceRacksMixin``, which provides ``_require_rack_device``.
    """

    def _require_variation_rack(self, track: int, device: DeviceLocator) -> Any:
        target_device = self._ctx._device_at(track, device)
        self._require_rack_device(target_device)
        if not hasattr(target_device, "variation_count"):
            raise _not_supported_by_live_api(
                message="Rack macro variations are not available in Live API",
                hint="Use a Live version exposing RackDevice.variation_count (Live 12+).",
            )
        return target_device

    def device_variations_list(self, track: int, device: DeviceLocator) -> dict[str, Any]:
        rack = self._require_variation_rack(track, device)
        return _variations_payload(track, device, rack)

    def device_variation_store(self, track: int, device: DeviceLocator) -> dict[str, Any]:
        rack = self._require_variation_rack(track, device)
        rack.store_variation()
        return _variations_payload(track, device, rack)

    def device_variation_recall(
        self, track: int, device: DeviceLocator, variation_index: int
    ) -> dict[str, Any]:
        rack = self._require_variation_rack(track, device)
        _select_variation(rack, variation_index)
        rack.recall_selected_variation()
        return _variations_payload(track, device, rack)

    def device_variation_delete(
        self, track: int, device: DeviceLocator, variation_index: int
    ) -> dict[str, Any]:
        rack = self._require_variation_rack(track, device)
        _select_variation(rack, variation_index)
        rack.delete_selected_variation()
        return _variations_payload(track, device, rack)


def _variations_payload(track: int, device: DeviceLocator, rack: Any) -> dict[str, Any]:
    return {
        "track": track,
        "device": device,
        "variation_count": int(rack.variation_count),
        "selected_variation_index": int(rack.selected_variation_index),
    }


def _select_variation(rack: Any, variation_index: int) -> None:
    count = int(rack.variation_count)
    if variation_index < 0 or variation_index >= count:
        hint = (
            f"Use a variation_index in 0..{count - 1} (see 'device variation list')."
            if count
            else "The rack has no stored variations; store one first."
        )
        raise _invalid_argument(
            message=f"variation_index out of range: {variation_index}",
            hint=hint,
        )
    rack.selected_variation_index = variation_index
