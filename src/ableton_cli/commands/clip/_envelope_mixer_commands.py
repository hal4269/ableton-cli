"""Clip envelopes for the track's own mixer: volume, panning and sends.

A separate subgroup (``clip envelope mixer ...``) rather than extra options on
``clip envelope set|shape|clear``: the target is a positional choice, so it can
never be combined with the device/parameter selectors.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Annotated, Any

import typer

from .._validation import invalid_argument
from ._envelope_commands import ENVELOPE_SHAPES, parse_points_json, shape_points
from ._shared import execute_clip_command, resolve_client, validate_track_and_clip

#: Mixer parameters a clip envelope can target, as Track.mixer_device exposes them.
MIXER_TARGETS = ("volume", "panning", "send")

TrackArgument = Annotated[int, typer.Argument(help="Track index (0-based)")]
ClipArgument = Annotated[int, typer.Argument(help="Clip slot index (0-based)")]
TargetArgument = Annotated[
    str,
    typer.Argument(
        help="volume (0-1, 0.85 = 0 dB) | panning (-1 to 1) | send (0-1, with --send-index)"
    ),
]
SendIndexOption = Annotated[
    int | None,
    typer.Option("--send-index", help="0-based send for target 'send' (0 = send A)"),
]


def register_envelope_mixer_commands(mixer_app: typer.Typer) -> None:
    mixer_app.command("set")(clip_envelope_mixer_set)
    mixer_app.command("shape")(clip_envelope_mixer_shape)
    mixer_app.command("clear")(clip_envelope_mixer_clear)


def mixer_target(target: str, send_index: int | None) -> dict[str, Any]:
    """Validate the mixer target; returns the client kwargs ``mixer`` and ``send_index``."""
    normalized = target.strip().lower()
    if normalized not in MIXER_TARGETS:
        raise invalid_argument(
            message=f"mixer target must be one of {', '.join(MIXER_TARGETS)}, got {target!r}",
            hint="Use volume, panning, or send with --send-index N.",
        )
    if normalized != "send":
        if send_index is not None:
            raise invalid_argument(
                message=f"--send-index only applies to target 'send', got {normalized!r}",
                hint="Drop --send-index, or use target 'send'.",
            )
        return {"mixer": normalized, "send_index": None}
    if send_index is None or send_index < 0:
        raise invalid_argument(
            message="target 'send' needs --send-index >= 0",
            hint="Pass the 0-based send index (0 = send A).",
        )
    return {"mixer": normalized, "send_index": send_index}


def _write_mixer_envelope(
    ctx: typer.Context,
    *,
    track: int,
    clip: int,
    target: str,
    send_index: int | None,
    points_factory: Callable[[], list[dict[str, Any]]],
) -> dict[str, object]:
    valid_track, valid_clip = validate_track_and_clip(track=track, clip=clip)
    target_kwargs = mixer_target(target, send_index)
    points = points_factory()
    return resolve_client(ctx).clip_envelope_set(
        valid_track, valid_clip, None, None, points, "replace", **target_kwargs
    )


def clip_envelope_mixer_set(
    ctx: typer.Context,
    track: TrackArgument,
    clip: ClipArgument,
    target: TargetArgument,
    points_json: Annotated[
        str, typer.Option("--points-json", help='JSON array of {"time","value"} breakpoints')
    ],
    send_index: SendIndexOption = None,
) -> None:
    """Write a clip envelope for the track's volume, panning or a send (replaces it)."""
    execute_clip_command(
        ctx,
        command="clip envelope mixer set",
        args={"track": track, "clip": clip, "target": target, "send_index": send_index},
        action=lambda: _write_mixer_envelope(
            ctx,
            track=track,
            clip=clip,
            target=target,
            send_index=send_index,
            points_factory=lambda: parse_points_json(points_json),
        ),
    )


def clip_envelope_mixer_shape(
    ctx: typer.Context,
    track: TrackArgument,
    clip: ClipArgument,
    target: TargetArgument,
    shape: Annotated[str, typer.Option("--shape", help=f"One of {', '.join(ENVELOPE_SHAPES)}")],
    from_value: Annotated[float, typer.Option("--from", help="Starting value")],
    to_value: Annotated[float, typer.Option("--to", help="Ending/target value")],
    send_index: SendIndexOption = None,
    start: Annotated[float, typer.Option("--start", help="Start time in beats")] = 0.0,
    length: Annotated[float, typer.Option("--length", help="Curve length in beats")] = 4.0,
    resolution: Annotated[
        int, typer.Option("--resolution", help="Number of breakpoints to generate")
    ] = 16,
    rate: Annotated[
        float, typer.Option("--rate", help="LFO cycles per beat of length (lfo-* shapes only)")
    ] = 1.0,
) -> None:
    """Write a generated curve (ramp, LFO, ...) on the track's volume, panning or a send."""
    execute_clip_command(
        ctx,
        command="clip envelope mixer shape",
        args={
            "track": track,
            "clip": clip,
            "target": target,
            "send_index": send_index,
            "shape": shape,
            "from": from_value,
            "to": to_value,
            "start": start,
            "length": length,
            "resolution": resolution,
            "rate": rate,
        },
        action=lambda: _write_mixer_envelope(
            ctx,
            track=track,
            clip=clip,
            target=target,
            send_index=send_index,
            points_factory=lambda: shape_points(
                shape,
                from_value=from_value,
                to_value=to_value,
                start=start,
                length=length,
                resolution=resolution,
                rate=rate,
            ),
        ),
    )


def clip_envelope_mixer_clear(
    ctx: typer.Context,
    track: TrackArgument,
    clip: ClipArgument,
    target: TargetArgument,
    send_index: SendIndexOption = None,
) -> None:
    """Clear the clip envelope of the track's volume, panning or a send."""

    def _run() -> dict[str, object]:
        valid_track, valid_clip = validate_track_and_clip(track=track, clip=clip)
        target_kwargs = mixer_target(target, send_index)
        return resolve_client(ctx).clip_envelope_clear(
            valid_track, valid_clip, clear_all=False, **target_kwargs
        )

    execute_clip_command(
        ctx,
        command="clip envelope mixer clear",
        args={"track": track, "clip": clip, "target": target, "send_index": send_index},
        action=_run,
    )
