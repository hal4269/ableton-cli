from __future__ import annotations

from typing import Annotated

import typer

from .._validation import invalid_argument, require_color_index
from ._shared import execute_track_clip_command

#: Clip.launch_mode values in Live's order.
LAUNCH_MODES: tuple[str, ...] = ("trigger", "gate", "toggle", "repeat")
#: Clip.launch_quantization values in Live's order ("8" = 8 bars, "1/4" = quarter note).
LAUNCH_QUANTIZATIONS: tuple[str, ...] = (
    "global",
    "none",
    "8",
    "4",
    "2",
    "1",
    "1/2",
    "1/2t",
    "1/4",
    "1/4t",
    "1/8",
    "1/8t",
    "1/16",
    "1/16t",
    "1/32",
)


def register_launch_commands(color_app: typer.Typer, launch_app: typer.Typer) -> None:
    color_app.command("set")(clip_color_set)
    launch_app.command("get")(clip_launch_get)
    launch_app.command("set")(clip_launch_set)


def clip_color_set(
    ctx: typer.Context,
    track: Annotated[int, typer.Argument(help="Track index (0-based)")],
    clip: Annotated[int, typer.Argument(help="Clip slot index (0-based)")],
    color_index: Annotated[int, typer.Argument(help="Color index in Live's color chooser (0-69)")],
) -> None:
    """Set a session clip's color."""

    def _action(client, valid_track: int, valid_clip: int) -> dict[str, object]:  # noqa: ANN001
        return client.clip_color_set(valid_track, valid_clip, require_color_index(color_index))

    execute_track_clip_command(
        ctx,
        command="clip color set",
        args={"track": track, "clip": clip, "color_index": color_index},
        track_clip=(track, clip),
        action=_action,
    )


def clip_launch_get(
    ctx: typer.Context,
    track: Annotated[int, typer.Argument(help="Track index (0-based)")],
    clip: Annotated[int, typer.Argument(help="Clip slot index (0-based)")],
) -> None:
    """Show a session clip's launch mode, quantization, legato and velocity amount."""
    execute_track_clip_command(
        ctx,
        command="clip launch get",
        args={"track": track, "clip": clip},
        track_clip=(track, clip),
        action=lambda client, valid_track, valid_clip: client.clip_launch_get(
            valid_track, valid_clip
        ),
    )


def _choice_index(name: str, value: str, choices: tuple[str, ...]) -> int:
    normalized = value.strip().lower()
    if normalized not in choices:
        raise invalid_argument(
            message=f"{name} must be one of {', '.join(choices)}, got {value!r}",
            hint=f"Pick a {name} from: {', '.join(choices)}.",
        )
    return choices.index(normalized)


def _launch_settings(
    *,
    mode: str | None,
    quantization: str | None,
    legato: bool | None,
    velocity_amount: float | None,
) -> dict[str, object]:
    settings: dict[str, object] = {}
    if mode is not None:
        settings["launch_mode"] = _choice_index("mode", mode, LAUNCH_MODES)
    if quantization is not None:
        settings["launch_quantization"] = _choice_index(
            "quantization", quantization, LAUNCH_QUANTIZATIONS
        )
    if legato is not None:
        settings["legato"] = legato
    if velocity_amount is not None:
        if velocity_amount < 0.0 or velocity_amount > 1.0:
            raise invalid_argument(
                message=f"velocity amount must be between 0.0 and 1.0, got {velocity_amount}",
                hint="Pass --velocity-amount 0.0 (no effect) to 1.0 (full effect).",
            )
        settings["velocity_amount"] = velocity_amount
    if not settings:
        raise invalid_argument(
            message="no launch setting given",
            hint="Pass --mode, --quantization, --legato/--no-legato or --velocity-amount.",
        )
    return settings


def clip_launch_set(
    ctx: typer.Context,
    track: Annotated[int, typer.Argument(help="Track index (0-based)")],
    clip: Annotated[int, typer.Argument(help="Clip slot index (0-based)")],
    mode: Annotated[
        str | None, typer.Option("--mode", help="trigger | gate | toggle | repeat")
    ] = None,
    quantization: Annotated[
        str | None,
        typer.Option(
            "--quantization",
            help="global | none | 8 | 4 | 2 | 1 (bars) | 1/2 ... 1/32, with t for triplets",
        ),
    ] = None,
    legato: Annotated[bool | None, typer.Option("--legato/--no-legato", help="Legato mode")] = None,
    velocity_amount: Annotated[
        float | None,
        typer.Option("--velocity-amount", help="How much note velocity sets clip volume (0-1)"),
    ] = None,
) -> None:
    """Change a session clip's launch settings; only the given options change."""
    args = {
        "track": track,
        "clip": clip,
        "mode": mode,
        "quantization": quantization,
        "legato": legato,
        "velocity_amount": velocity_amount,
    }

    def _action(client, valid_track: int, valid_clip: int) -> dict[str, object]:  # noqa: ANN001
        settings = _launch_settings(
            mode=mode,
            quantization=quantization,
            legato=legato,
            velocity_amount=velocity_amount,
        )
        return client.clip_launch_set(valid_track, valid_clip, settings)

    execute_track_clip_command(
        ctx,
        command="clip launch set",
        args=args,
        track_clip=(track, clip),
        action=_action,
    )
