from __future__ import annotations

from typing import Annotated

import typer

from .._validation import require_time_signature
from ._shared import execute_track_clip_command


def register_edit_commands(clip_app: typer.Typer, signature_app: typer.Typer) -> None:
    clip_app.command("crop")(clip_crop)
    clip_app.command("duplicate-loop")(clip_duplicate_loop)
    signature_app.command("set")(clip_signature_set)


def clip_crop(
    ctx: typer.Context,
    track: Annotated[int, typer.Argument(help="Track index (0-based)")],
    clip: Annotated[int, typer.Argument(help="Clip slot index (0-based)")],
) -> None:
    """Crop a session clip to its loop (or to its start/end markers when not looping)."""
    execute_track_clip_command(
        ctx,
        command="clip crop",
        args={"track": track, "clip": clip},
        track_clip=(track, clip),
        action=lambda client, valid_track, valid_clip: client.clip_crop(valid_track, valid_clip),
    )


def clip_duplicate_loop(
    ctx: typer.Context,
    track: Annotated[int, typer.Argument(help="Track index (0-based)")],
    clip: Annotated[int, typer.Argument(help="Clip slot index (0-based)")],
) -> None:
    """Double a MIDI clip's loop, copying its notes and envelopes into the new half."""
    execute_track_clip_command(
        ctx,
        command="clip duplicate-loop",
        args={"track": track, "clip": clip},
        track_clip=(track, clip),
        action=lambda client, valid_track, valid_clip: client.clip_duplicate_loop(
            valid_track, valid_clip
        ),
    )


def clip_signature_set(
    ctx: typer.Context,
    track: Annotated[int, typer.Argument(help="Track index (0-based)")],
    clip: Annotated[int, typer.Argument(help="Clip slot index (0-based)")],
    numerator: Annotated[int, typer.Argument(help="Beats per bar (1-99)")],
    denominator: Annotated[int, typer.Argument(help="Note value: 1, 2, 4, 8 or 16")],
) -> None:
    """Set a session clip's time signature."""

    def _action(client, valid_track: int, valid_clip: int) -> dict[str, object]:  # noqa: ANN001
        valid_numerator, valid_denominator = require_time_signature(numerator, denominator)
        return client.clip_signature_set(
            valid_track, valid_clip, valid_numerator, valid_denominator
        )

    execute_track_clip_command(
        ctx,
        command="clip signature set",
        args={"track": track, "clip": clip, "numerator": numerator, "denominator": denominator},
        track_clip=(track, clip),
        action=_action,
    )
