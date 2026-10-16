from __future__ import annotations

from collections.abc import Callable
from typing import Annotated

import typer

from ..runtime import execute_command, get_client
from ..song_settings_names import (
    CAPTURE_DESTINATIONS,
    GROOVE_AMOUNT_MAX,
    RECORD_QUANTIZATION_NAMES,
    ROOT_NOTES,
    SWING_AMOUNT_MAX,
)
from ._client_command_runner import CommandSpec
from ._client_command_runner import run_client_command as run_client_command_shared
from ._client_command_runner import run_client_command_spec as run_client_command_spec_shared
from ._validation import (
    invalid_argument,
    require_choice,
    require_float_in_range,
    require_non_empty_string,
    require_non_negative_float,
    require_positive_float,
)

song_app = typer.Typer(help="Song and session information", no_args_is_help=True)
loop_app = typer.Typer(help="Arrangement loop region", no_args_is_help=True)
metronome_app = typer.Typer(help="Metronome", no_args_is_help=True)
swing_app = typer.Typer(help="Global swing amount (Song.swing_amount)", no_args_is_help=True)
groove_amount_app = typer.Typer(
    help="Groove Pool global amount (Song.groove_amount)", no_args_is_help=True
)
scale_app = typer.Typer(help="Song key and scale (Live 12+)", no_args_is_help=True)
record_quantization_app = typer.Typer(
    help="MIDI record quantization (Song.midi_recording_quantization)", no_args_is_help=True
)


SongCommandSpec = CommandSpec


SONG_INFO_SPEC = SongCommandSpec(
    command_name="song info",
    client_method="song_info",
)
SONG_NEW_SPEC = SongCommandSpec(
    command_name="song new",
    client_method="song_new",
)
SONG_UNDO_SPEC = SongCommandSpec(
    command_name="song undo",
    client_method="song_undo",
)
SONG_REDO_SPEC = SongCommandSpec(
    command_name="song redo",
    client_method="song_redo",
)
SONG_LOOP_GET_SPEC = SongCommandSpec(command_name="song loop get", client_method="song_loop_get")
SONG_LOOP_SET_SPEC = SongCommandSpec(command_name="song loop set", client_method="song_loop_set")
SONG_METRONOME_SET_SPEC = SongCommandSpec(
    command_name="song metronome set", client_method="song_metronome_set"
)
SONG_SWING_SET_SPEC = SongCommandSpec(command_name="song swing set", client_method="song_swing_set")
SONG_GROOVE_AMOUNT_SET_SPEC = SongCommandSpec(
    command_name="song groove-amount set", client_method="song_groove_amount_set"
)
SONG_SCALE_SET_SPEC = SongCommandSpec(command_name="song scale set", client_method="song_scale_set")
SONG_RECORD_QUANTIZATION_SET_SPEC = SongCommandSpec(
    command_name="song record-quantization set", client_method="song_record_quantization_set"
)
SONG_CAPTURE_MIDI_SPEC = SongCommandSpec(
    command_name="song capture-midi", client_method="song_capture_midi"
)


def run_client_command(
    ctx: typer.Context,
    *,
    command_name: str,
    args: dict[str, object],
    fn: Callable[[object], dict[str, object]],
) -> None:
    run_client_command_shared(
        ctx,
        command_name=command_name,
        args=args,
        fn=fn,
        get_client_fn=get_client,
        execute_command_fn=execute_command,
    )


def run_client_command_spec(
    ctx: typer.Context,
    *,
    spec: SongCommandSpec,
    args: dict[str, object],
    method_kwargs: dict[str, object] | Callable[[], dict[str, object]] | None = None,
) -> None:
    run_client_command_spec_shared(
        ctx,
        spec=spec,
        args=args,
        method_kwargs=method_kwargs,
        get_client_fn=get_client,
        execute_command_fn=execute_command,
    )


@song_app.command("info")
def song_info(ctx: typer.Context) -> None:
    run_client_command_spec(
        ctx,
        spec=SONG_INFO_SPEC,
        args={},
    )


@song_app.command("new")
def song_new(ctx: typer.Context) -> None:
    run_client_command_spec(
        ctx,
        spec=SONG_NEW_SPEC,
        args={},
    )


@song_app.command("undo")
def song_undo(ctx: typer.Context) -> None:
    run_client_command_spec(
        ctx,
        spec=SONG_UNDO_SPEC,
        args={},
    )


@song_app.command("redo")
def song_redo(ctx: typer.Context) -> None:
    run_client_command_spec(
        ctx,
        spec=SONG_REDO_SPEC,
        args={},
    )


def _non_empty_settings(settings: dict[str, object], options: str) -> dict[str, object]:
    present = {key: value for key, value in settings.items() if value is not None}
    if not present:
        raise invalid_argument(message="no setting given", hint=f"Pass at least one of {options}.")
    return present


@loop_app.command("get")
def song_loop_get(ctx: typer.Context) -> None:
    """Show the Arrangement loop: enabled, start, length and end (beats)."""
    run_client_command_spec(ctx, spec=SONG_LOOP_GET_SPEC, args={})


@loop_app.command("set")
def song_loop_set(
    ctx: typer.Context,
    enabled: Annotated[
        bool | None,
        typer.Option("--enabled/--disabled", help="Switch the Arrangement loop on or off"),
    ] = None,
    start: Annotated[float | None, typer.Option("--start", help="Loop start in beats")] = None,
    length: Annotated[float | None, typer.Option("--length", help="Loop length in beats")] = None,
) -> None:
    """Change the Arrangement loop region; options left out keep their value."""
    args: dict[str, object] = {"enabled": enabled, "start": start, "length": length}

    def _method_kwargs() -> dict[str, object]:
        if start is not None:
            require_non_negative_float("start", start, hint="Use a loop start >= 0 beats.")
        if length is not None:
            require_positive_float("length", length, hint="Use a loop length > 0 beats.")
        return {"settings": _non_empty_settings(args, "--enabled/--disabled, --start, --length")}

    run_client_command_spec(ctx, spec=SONG_LOOP_SET_SPEC, args=args, method_kwargs=_method_kwargs)


@metronome_app.command("set")
def song_metronome_set(
    ctx: typer.Context,
    value: Annotated[bool, typer.Argument(help="Metronome on: true|false")],
) -> None:
    """Switch the metronome on or off."""
    run_client_command_spec(
        ctx, spec=SONG_METRONOME_SET_SPEC, args={"value": value}, method_kwargs={"value": value}
    )


def _amount_setter(
    spec: SongCommandSpec, maximum: float, hint: str
) -> Callable[[typer.Context, float], None]:
    def _set(ctx: typer.Context, value: float) -> None:
        run_client_command_spec(
            ctx,
            spec=spec,
            args={"value": value},
            method_kwargs=lambda: {
                "value": require_float_in_range(
                    "value", value, minimum=0.0, maximum=maximum, hint=hint
                )
            },
        )

    return _set


_set_swing = _amount_setter(SONG_SWING_SET_SPEC, SWING_AMOUNT_MAX, "Use a swing amount 0.0-1.0.")
_set_groove_amount = _amount_setter(
    SONG_GROOVE_AMOUNT_SET_SPEC,
    GROOVE_AMOUNT_MAX,
    f"Use a groove amount 0.0-{GROOVE_AMOUNT_MAX} (0-130%).",
)


@swing_app.command("set")
def song_swing_set(
    ctx: typer.Context,
    value: Annotated[float, typer.Argument(help="Swing amount 0.0-1.0")],
) -> None:
    """Set the global swing amount (applies to MIDI recording quantization and quantize)."""
    _set_swing(ctx, value)


@groove_amount_app.command("set")
def song_groove_amount_set(
    ctx: typer.Context,
    value: Annotated[float, typer.Argument(help="Global groove amount 0.0-1.3 (0-130%)")],
) -> None:
    """Set the Groove Pool's global amount."""
    _set_groove_amount(ctx, value)


def _root_note(value: str) -> int:
    if value.isdigit():
        root = int(value)
        if root <= 11:
            return root
    elif value.upper() in ROOT_NOTES:
        return ROOT_NOTES[value.upper()]
    raise invalid_argument(
        message=f"invalid root note {value!r}",
        hint="Use a note name (C, C#, Db ... B) or 0-11.",
    )


@scale_app.command("set")
def song_scale_set(
    ctx: typer.Context,
    root: Annotated[
        str | None, typer.Option("--root", help="Root note: C, C#, Db ... B, or 0-11")
    ] = None,
    name: Annotated[
        str | None, typer.Option("--name", help="Scale name as shown in Live (e.g. Minor)")
    ] = None,
    mode: Annotated[
        bool | None,
        typer.Option("--mode/--no-mode", help="Scale mode (highlight/fold to scale) on or off"),
    ] = None,
) -> None:
    """Set the song key (root note), scale name and/or scale mode (Live 12+)."""

    def _method_kwargs() -> dict[str, object]:
        settings: dict[str, object] = {"mode": mode}
        if root is not None:
            settings["root_note"] = _root_note(root)
        if name is not None:
            settings["name"] = require_non_empty_string(
                "name", name, hint="Pass a scale name as shown in Live."
            )
        return {"settings": _non_empty_settings(settings, "--root, --name, --mode/--no-mode")}

    run_client_command_spec(
        ctx,
        spec=SONG_SCALE_SET_SPEC,
        args={"root": root, "name": name, "mode": mode},
        method_kwargs=_method_kwargs,
    )


@record_quantization_app.command("set")
def song_record_quantization_set(
    ctx: typer.Context,
    value: Annotated[str, typer.Argument(help=f"One of: {', '.join(RECORD_QUANTIZATION_NAMES)}")],
) -> None:
    """Set the quantization applied while recording MIDI."""
    run_client_command_spec(
        ctx,
        spec=SONG_RECORD_QUANTIZATION_SET_SPEC,
        args={"value": value},
        method_kwargs=lambda: {"value": require_choice("value", value, RECORD_QUANTIZATION_NAMES)},
    )


@song_app.command("capture-midi")
def song_capture_midi(
    ctx: typer.Context,
    destination: Annotated[
        str,
        typer.Option("--destination", help="auto, session or arrangement"),
    ] = "auto",
) -> None:
    """Capture the MIDI Live recently heard on armed/monitoring tracks into a clip."""
    run_client_command_spec(
        ctx,
        spec=SONG_CAPTURE_MIDI_SPEC,
        args={"destination": destination},
        method_kwargs=lambda: {
            "destination": require_choice("destination", destination, CAPTURE_DESTINATIONS)
        },
    )


song_app.add_typer(loop_app, name="loop")
song_app.add_typer(metronome_app, name="metronome")
song_app.add_typer(swing_app, name="swing")
song_app.add_typer(groove_amount_app, name="groove-amount")
song_app.add_typer(scale_app, name="scale")
song_app.add_typer(record_quantization_app, name="record-quantization")


def register(app: typer.Typer) -> None:
    app.add_typer(song_app, name="song")
