from __future__ import annotations

from typing import Any

import pytest
from test_live_backend import _Clip, _ClipSlot, _SurfaceStub

from remote_script.AbletonCliRemote.command_backend import CommandError, dispatch_command
from remote_script.AbletonCliRemote.live_backend import LiveBackend


class _EditableClip(_Clip):
    """A session clip with Live's loop, signature, crop and duplicate_loop API."""

    def __init__(self, length: float, *, is_midi_clip: bool = True) -> None:
        super().__init__(length=length, is_audio_clip=not is_midi_clip, is_midi_clip=is_midi_clip)
        self.loop_start = 0.0
        self.loop_end = float(length)
        self.looping = True
        self.signature_numerator = 4
        self.signature_denominator = 4

    def crop(self) -> None:
        # Live removes everything outside the loop (or the start/end markers).
        self.length = self.loop_end - self.loop_start
        self.loop_end = self.length
        self.loop_start = 0.0
        self.start_marker = 0.0
        self.end_marker = self.length

    def duplicate_loop(self) -> None:
        loop_length = self.loop_end - self.loop_start
        self.loop_end += loop_length
        self.end_marker = self.loop_end
        self.length = self.loop_end - self.loop_start


def _backend_with_clip(clip: Any) -> LiveBackend:
    backend = LiveBackend(_SurfaceStub())
    slot: _ClipSlot = backend.context._clip_slot_at(0, 0)
    slot.clip = clip
    return backend


def test_clip_crop_keeps_only_the_loop() -> None:
    clip = _EditableClip(8.0)
    clip.loop_start = 2.0
    clip.loop_end = 6.0
    backend = _backend_with_clip(clip)

    result = dispatch_command(backend, "clip_crop", {"track": 0, "clip": 0})

    assert result["length"] == 4.0
    assert (result["loop_start"], result["loop_end"]) == (0.0, 4.0)


def test_clip_duplicate_loop_doubles_the_loop() -> None:
    backend = _backend_with_clip(_EditableClip(4.0))

    result = dispatch_command(backend, "clip_duplicate_loop", {"track": 0, "clip": 0})

    assert (result["loop_start"], result["loop_end"], result["length"]) == (0.0, 8.0, 8.0)


def test_clip_duplicate_loop_requires_a_midi_clip() -> None:
    backend = _backend_with_clip(_EditableClip(4.0, is_midi_clip=False))

    with pytest.raises(CommandError) as exc_info:
        dispatch_command(backend, "clip_duplicate_loop", {"track": 0, "clip": 0})

    assert exc_info.value.code == "INVALID_ARGUMENT"
    assert "MIDI" in exc_info.value.message


@pytest.mark.parametrize("command", ["clip_crop", "clip_duplicate_loop"])
def test_clip_edit_fails_explicitly_when_live_lacks_the_method(command: str) -> None:
    backend = _backend_with_clip(_Clip(length=4.0))

    with pytest.raises(CommandError) as exc_info:
        dispatch_command(backend, command, {"track": 0, "clip": 0})

    assert exc_info.value.details == {"reason": "not_supported_by_live_api"}


@pytest.mark.parametrize("command", ["clip_crop", "clip_duplicate_loop"])
def test_clip_edit_requires_a_clip(command: str) -> None:
    backend = LiveBackend(_SurfaceStub())

    with pytest.raises(CommandError) as exc_info:
        dispatch_command(backend, command, {"track": 0, "clip": 0})

    assert exc_info.value.code == "INVALID_ARGUMENT"


def test_clip_signature_set_and_props_show_it() -> None:
    backend = _backend_with_clip(_EditableClip(4.0))

    result = dispatch_command(
        backend,
        "clip_signature_set",
        {"track": 0, "clip": 0, "numerator": 7, "denominator": 8},
    )

    assert (result["signature_numerator"], result["signature_denominator"]) == (7, 8)
    props = dispatch_command(backend, "clip_props_get", {"track": 0, "clip": 0})
    assert (props["signature_numerator"], props["signature_denominator"]) == (7, 8)


@pytest.mark.parametrize(("numerator", "denominator"), [(0, 4), (100, 4), (4, 3), (4, 32)])
def test_clip_signature_set_rejects_invalid_signatures(numerator: int, denominator: int) -> None:
    backend = _backend_with_clip(_EditableClip(4.0))

    with pytest.raises(CommandError) as exc_info:
        dispatch_command(
            backend,
            "clip_signature_set",
            {"track": 0, "clip": 0, "numerator": numerator, "denominator": denominator},
        )

    assert exc_info.value.code == "INVALID_ARGUMENT"
