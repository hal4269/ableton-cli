from __future__ import annotations

from typing import Any

from ..refs import RefPayload


class _AbletonClientTracksClipsMixin:
    def _call_clip_note_transform(
        self,
        command_name: str,
        *,
        track: int,
        clip: int,
        extra_args: dict[str, Any],
        start_time: float | None,
        end_time: float | None,
        pitch: int | None,
    ) -> dict[str, Any]:
        args = self._build_clip_note_args(
            track=track,
            clip=clip,
            notes=None,
            start_time=start_time,
            end_time=end_time,
            pitch=pitch,
        )
        args.update(extra_args)
        return self._call(command_name, args)

    def add_notes_to_clip(
        self,
        track: int,
        clip: int,
        notes: list[dict[str, Any]],
    ) -> dict[str, Any]:
        args = self._build_clip_note_args(
            track=track,
            clip=clip,
            notes=notes,
            start_time=None,
            end_time=None,
            pitch=None,
        )
        return self._call("add_notes_to_clip", args)

    def update_clip_notes(
        self,
        track: int,
        clip: int,
        notes: list[dict[str, Any]],
    ) -> dict[str, Any]:
        args = self._build_clip_note_args(
            track=track,
            clip=clip,
            notes=notes,
            start_time=None,
            end_time=None,
            pitch=None,
        )
        return self._call("update_clip_notes", args)

    def get_clip_notes(
        self,
        track: int,
        clip: int,
        start_time: float | None,
        end_time: float | None,
        pitch: int | None,
    ) -> dict[str, Any]:
        args = self._build_clip_note_args(
            track=track,
            clip=clip,
            notes=None,
            start_time=start_time,
            end_time=end_time,
            pitch=pitch,
        )
        return self._call("get_clip_notes", args)

    def clear_clip_notes(
        self,
        track: int,
        clip: int,
        start_time: float | None,
        end_time: float | None,
        pitch: int | None,
    ) -> dict[str, Any]:
        args = self._build_clip_note_args(
            track=track,
            clip=clip,
            notes=None,
            start_time=start_time,
            end_time=end_time,
            pitch=pitch,
        )
        return self._call("clear_clip_notes", args)

    def replace_clip_notes(
        self,
        track: int,
        clip: int,
        notes: list[dict[str, Any]],
        start_time: float | None,
        end_time: float | None,
        pitch: int | None,
    ) -> dict[str, Any]:
        args = self._build_clip_note_args(
            track=track,
            clip=clip,
            notes=notes,
            start_time=start_time,
            end_time=end_time,
            pitch=pitch,
        )
        return self._call("replace_clip_notes", args)

    def _add_envelope_target(
        self,
        args: dict[str, Any],
        *,
        device_ref: RefPayload | None,
        parameter_ref: RefPayload | None,
        mixer: str | None,
        send_index: int | None,
    ) -> None:
        self._add_if_not_none(args, "device_ref", device_ref)
        self._add_if_not_none(args, "parameter_ref", parameter_ref)
        self._add_if_not_none(args, "mixer", mixer)
        self._add_if_not_none(args, "send_index", send_index)

    def clip_envelope_set(
        self,
        track: int,
        clip: int,
        device_ref: RefPayload | None,
        parameter_ref: RefPayload | None,
        points: list[dict[str, float]],
        mode: str = "replace",
        mixer: str | None = None,
        send_index: int | None = None,
    ) -> dict[str, Any]:
        """Target a device parameter (device_ref + parameter_ref) or the track
        mixer (mixer = volume | panning | send, send_index for sends)."""
        args: dict[str, Any] = {"track": track, "clip": clip, "points": points, "mode": mode}
        self._add_envelope_target(
            args,
            device_ref=device_ref,
            parameter_ref=parameter_ref,
            mixer=mixer,
            send_index=send_index,
        )
        return self._call("clip_envelope_set", args)

    def clip_envelope_clear(
        self,
        track: int,
        clip: int,
        device_ref: RefPayload | None = None,
        parameter_ref: RefPayload | None = None,
        clear_all: bool = False,
        mixer: str | None = None,
        send_index: int | None = None,
    ) -> dict[str, Any]:
        args: dict[str, Any] = {"track": track, "clip": clip, "clear_all": clear_all}
        self._add_envelope_target(
            args,
            device_ref=device_ref,
            parameter_ref=parameter_ref,
            mixer=mixer,
            send_index=send_index,
        )
        return self._call("clip_envelope_clear", args)

    def clip_notes_quantize(
        self,
        track: int,
        clip: int,
        grid: str,
        strength: float,
        start_time: float | None,
        end_time: float | None,
        pitch: int | None,
    ) -> dict[str, Any]:
        return self._call_clip_note_transform(
            "clip_notes_quantize",
            track=track,
            clip=clip,
            extra_args={"grid": grid, "strength": strength},
            start_time=start_time,
            end_time=end_time,
            pitch=pitch,
        )

    def clip_notes_humanize(
        self,
        track: int,
        clip: int,
        timing: float,
        velocity: int,
        start_time: float | None,
        end_time: float | None,
        pitch: int | None,
    ) -> dict[str, Any]:
        return self._call_clip_note_transform(
            "clip_notes_humanize",
            track=track,
            clip=clip,
            extra_args={"timing": timing, "velocity": velocity},
            start_time=start_time,
            end_time=end_time,
            pitch=pitch,
        )

    def clip_notes_velocity_scale(
        self,
        track: int,
        clip: int,
        scale: float,
        offset: int,
        start_time: float | None,
        end_time: float | None,
        pitch: int | None,
    ) -> dict[str, Any]:
        return self._call_clip_note_transform(
            "clip_notes_velocity_scale",
            track=track,
            clip=clip,
            extra_args={"scale": scale, "offset": offset},
            start_time=start_time,
            end_time=end_time,
            pitch=pitch,
        )

    def clip_notes_transpose(
        self,
        track: int,
        clip: int,
        semitones: int,
        start_time: float | None,
        end_time: float | None,
        pitch: int | None,
    ) -> dict[str, Any]:
        return self._call_clip_note_transform(
            "clip_notes_transpose",
            track=track,
            clip=clip,
            extra_args={"semitones": semitones},
            start_time=start_time,
            end_time=end_time,
            pitch=pitch,
        )

    def clip_warp_set(
        self,
        track: int,
        clip: int,
        enabled: bool,
        mode: str | None,
    ) -> dict[str, Any]:
        args: dict[str, Any] = {"track": track, "clip": clip, "enabled": enabled}
        self._add_if_not_none(args, "mode", mode)
        return self._call("clip_warp_set", args)

    def clip_warp_marker_add(
        self,
        track: int,
        clip: int,
        beat_time: float,
        sample_time: float | None = None,
    ) -> dict[str, Any]:
        args: dict[str, Any] = {"track": track, "clip": clip, "beat_time": beat_time}
        self._add_if_not_none(args, "sample_time", sample_time)
        return self._call("clip_warp_marker_add", args)

    def clip_duplicate(
        self,
        track: int,
        src_clip: int,
        dst_clip: int | None = None,
        dst_clips: list[int] | None = None,
    ) -> dict[str, Any]:
        args: dict[str, Any] = {"track": track, "src_clip": src_clip}
        self._add_if_not_none(args, "dst_clip", dst_clip)
        self._add_if_not_none(args, "dst_clips", dst_clips)
        return self._call("clip_duplicate", args)
