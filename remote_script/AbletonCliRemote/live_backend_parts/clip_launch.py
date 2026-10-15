from __future__ import annotations

from typing import Any

from .base import _invalid_argument

#: Live's color chooser has 70 colors; color_index addresses them directly.
COLOR_INDEX_COUNT = 70

_LAUNCH_FIELDS = ("launch_mode", "launch_quantization", "legato", "velocity_amount")


class LiveBackendClipLaunchMixin:
    """Track/clip colors and session clip launch settings."""

    def track_color_set(self, track: int, color_index: int) -> dict[str, Any]:
        target = self._ctx._track_at(track)
        target.color_index = color_index
        return {"track": track, "color_index": int(target.color_index)}

    def _session_clip(self, track: int, clip: int) -> Any:
        slot = self._ctx._clip_slot_at(track, clip)
        if not slot.has_clip:
            raise _invalid_argument(
                message="No clip in slot",
                hint="Pass a clip slot that holds a clip.",
            )
        return slot.clip

    def clip_color_set(self, track: int, clip: int, color_index: int) -> dict[str, Any]:
        target = self._session_clip(track, clip)
        target.color_index = color_index
        return {"track": track, "clip": clip, "color_index": int(target.color_index)}

    @staticmethod
    def _launch_payload(track: int, clip: int, target: Any) -> dict[str, Any]:
        return {
            "track": track,
            "clip": clip,
            "launch_mode": int(target.launch_mode),
            "launch_quantization": int(target.launch_quantization),
            "legato": bool(target.legato),
            "velocity_amount": float(target.velocity_amount),
        }

    def clip_launch_get(self, track: int, clip: int) -> dict[str, Any]:
        return self._launch_payload(track, clip, self._session_clip(track, clip))

    def clip_launch_set(self, track: int, clip: int, settings: dict[str, Any]) -> dict[str, Any]:
        target = self._session_clip(track, clip)
        for field in _LAUNCH_FIELDS:
            if settings.get(field) is not None:
                setattr(target, field, settings[field])
        return self._launch_payload(track, clip, target)
