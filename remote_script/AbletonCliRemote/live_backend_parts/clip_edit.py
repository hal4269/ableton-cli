from __future__ import annotations

from typing import Any

from .base import _invalid_argument, _not_supported_by_live_api


class LiveBackendClipEditMixin:
    """Session clip edits that Live performs itself: crop, duplicate loop, signature.

    Lives in the tracks/clips service so it can reuse the session-clip lookup and
    the ``clip props get`` payload, which every command here returns.
    """

    def _call_clip_method(self, clip_obj: Any, method_name: str) -> None:
        method = getattr(clip_obj, method_name, None)
        if not callable(method):
            raise _not_supported_by_live_api(
                message=f"Clip.{method_name} is not available in Live API",
                hint=f"Use a Live version exposing clip.{method_name}() (Live 12+).",
            )
        method()

    def clip_crop(self, track: int, clip: int) -> dict[str, Any]:
        clip_obj = self._require_session_clip(track, clip, action="cropping it")
        self._call_clip_method(clip_obj, "crop")
        return self.clip_props_get(track, clip)

    def clip_duplicate_loop(self, track: int, clip: int) -> dict[str, Any]:
        clip_obj = self._require_session_clip(track, clip, action="duplicating its loop")
        if not bool(getattr(clip_obj, "is_midi_clip", False)):
            raise _invalid_argument(
                message="clip must be a MIDI clip to duplicate its loop",
                hint="Live's Duplicate Loop works on MIDI clips only.",
            )
        self._call_clip_method(clip_obj, "duplicate_loop")
        return self.clip_props_get(track, clip)

    def clip_signature_set(
        self, track: int, clip: int, numerator: int, denominator: int
    ) -> dict[str, Any]:
        clip_obj = self._require_session_clip(track, clip, action="setting its signature")
        self._set_required_clip_attr(
            clip_obj, "signature_numerator", numerator, api_name="signature numerator"
        )
        self._set_required_clip_attr(
            clip_obj, "signature_denominator", denominator, api_name="signature denominator"
        )
        return self.clip_props_get(track, clip)
