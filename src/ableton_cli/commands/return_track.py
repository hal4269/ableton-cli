from __future__ import annotations

from typing import Annotated

import typer

from ..runtime import execute_command, get_client
from ._track_shared import ReturnTrackArgument, VolumeValueArgument
from ._validation import VOLUME_VALUE_HINT, require_float_in_range, require_non_negative

RETURN_TRACK_INDEX_HINT = "Use a valid return track index from 'return-tracks list'."

return_track_app = typer.Typer(help="Single return-track commands", no_args_is_help=True)
volume_app = typer.Typer(help="Return-track volume commands", no_args_is_help=True)
mute_app = typer.Typer(help="Return-track mute commands", no_args_is_help=True)
solo_app = typer.Typer(help="Return-track solo commands", no_args_is_help=True)
name_app = typer.Typer(help="Return-track name commands", no_args_is_help=True)
device_app = typer.Typer(help="Return-track device commands", no_args_is_help=True)
device_parameter_app = typer.Typer(
    help="Return-track device parameter commands", no_args_is_help=True
)

DeviceIndexArgument = Annotated[int, typer.Argument(help="Device index on the return track")]


def _require_return_track_index(return_track: int) -> int:
    return require_non_negative("return_track", return_track, hint=RETURN_TRACK_INDEX_HINT)


def _require_return_track_and_volume(return_track: int, value: float) -> tuple[int, float]:
    valid_track = _require_return_track_index(return_track)
    valid_value = require_float_in_range(
        "value",
        value,
        minimum=0.0,
        maximum=1.0,
        hint=VOLUME_VALUE_HINT,
    )
    return valid_track, valid_value


def run_return_track_command(
    ctx: typer.Context,
    *,
    command_name: str,
    return_track: int,
    fn,
) -> None:
    def _run() -> dict[str, object]:
        valid_return_track = _require_return_track_index(return_track)
        client = get_client(ctx)
        return fn(client, valid_return_track)

    execute_command(
        ctx,
        command=command_name,
        args={"return_track": return_track},
        action=_run,
    )


def run_return_track_value_command(
    ctx: typer.Context,
    *,
    command_name: str,
    return_track: int,
    value,
    fn,
    validator,
) -> None:
    def _run() -> dict[str, object]:
        valid_return_track, valid_value = validator(return_track, value)
        client = get_client(ctx)
        return fn(client, valid_return_track, valid_value)

    execute_command(
        ctx,
        command=command_name,
        args={"return_track": return_track, "value": value},
        action=_run,
    )


@volume_app.command("get")
def return_track_volume_get(
    ctx: typer.Context,
    return_track: ReturnTrackArgument,
) -> None:
    run_return_track_command(
        ctx,
        command_name="return-track volume get",
        return_track=return_track,
        fn=lambda client, valid_return_track: client.return_track_volume_get(valid_return_track),
    )


@volume_app.command("set")
def return_track_volume_set(
    ctx: typer.Context,
    return_track: ReturnTrackArgument,
    value: VolumeValueArgument,
) -> None:
    run_return_track_value_command(
        ctx,
        command_name="return-track volume set",
        return_track=return_track,
        value=value,
        fn=lambda client, valid_return_track, valid_value: client.return_track_volume_set(
            valid_return_track,
            valid_value,
        ),
        validator=_require_return_track_and_volume,
    )


@mute_app.command("get")
def return_track_mute_get(
    ctx: typer.Context,
    return_track: ReturnTrackArgument,
) -> None:
    run_return_track_command(
        ctx,
        command_name="return-track mute get",
        return_track=return_track,
        fn=lambda client, valid_return_track: client.return_track_mute_get(valid_return_track),
    )


@mute_app.command("set")
def return_track_mute_set(
    ctx: typer.Context,
    return_track: ReturnTrackArgument,
    value: Annotated[bool, typer.Argument(help="Mute value: true|false")],
) -> None:
    run_return_track_value_command(
        ctx,
        command_name="return-track mute set",
        return_track=return_track,
        value=value,
        fn=lambda client, valid_return_track, valid_value: client.return_track_mute_set(
            valid_return_track,
            valid_value,
        ),
        validator=lambda track_index, mute_value: (
            _require_return_track_index(track_index),
            mute_value,
        ),
    )


@solo_app.command("get")
def return_track_solo_get(
    ctx: typer.Context,
    return_track: ReturnTrackArgument,
) -> None:
    run_return_track_command(
        ctx,
        command_name="return-track solo get",
        return_track=return_track,
        fn=lambda client, valid_return_track: client.return_track_solo_get(valid_return_track),
    )


@solo_app.command("set")
def return_track_solo_set(
    ctx: typer.Context,
    return_track: ReturnTrackArgument,
    value: Annotated[bool, typer.Argument(help="Solo value: true|false")],
) -> None:
    run_return_track_value_command(
        ctx,
        command_name="return-track solo set",
        return_track=return_track,
        value=value,
        fn=lambda client, valid_return_track, valid_value: client.return_track_solo_set(
            valid_return_track,
            valid_value,
        ),
        validator=lambda track_index, solo_value: (
            _require_return_track_index(track_index),
            solo_value,
        ),
    )


def _run_return_track_args(ctx: typer.Context, command_name: str, args: dict, fn) -> None:
    def _run() -> dict[str, object]:
        _require_return_track_index(args["return_track"])
        if "device" in args:
            require_non_negative("device", args["device"], hint="Use 'return-track device list'.")
        return fn(get_client(ctx))

    execute_command(ctx, command=command_name, args=args, action=_run)


@name_app.command("set")
def return_track_name_set(
    ctx: typer.Context,
    return_track: ReturnTrackArgument,
    name: Annotated[str, typer.Argument(help="New return-track name")],
) -> None:
    _run_return_track_args(
        ctx,
        "return-track name set",
        {"return_track": return_track, "name": name},
        lambda client: client.return_track_name_set(return_track, name),
    )


@device_app.command("list")
def return_track_devices_list(ctx: typer.Context, return_track: ReturnTrackArgument) -> None:
    _run_return_track_args(
        ctx,
        "return-track device list",
        {"return_track": return_track},
        lambda client: client.return_track_devices_list(return_track),
    )


@device_app.command("insert")
def return_track_device_insert(
    ctx: typer.Context,
    return_track: ReturnTrackArgument,
    device_name: Annotated[str, typer.Argument(help="Native Live device name, e.g. 'Echo'")],
    index: Annotated[
        int | None, typer.Option("--index", help="Position in the chain (default: append)")
    ] = None,
) -> None:
    _run_return_track_args(
        ctx,
        "return-track device insert",
        {"return_track": return_track, "device_name": device_name, "index": index},
        lambda client: client.return_track_device_insert(return_track, device_name, index),
    )


@device_app.command("parameters")
def return_track_device_parameters_list(
    ctx: typer.Context,
    return_track: ReturnTrackArgument,
    device: DeviceIndexArgument,
) -> None:
    _run_return_track_args(
        ctx,
        "return-track device parameters",
        {"return_track": return_track, "device": device},
        lambda client: client.return_track_device_parameters_list(return_track, device),
    )


@device_parameter_app.command("set-display")
def return_track_device_parameter_set_display(
    ctx: typer.Context,
    return_track: ReturnTrackArgument,
    device: DeviceIndexArgument,
    parameter: Annotated[str, typer.Argument(help="Exact parameter name")],
    display: Annotated[str, typer.Argument(help="Display value, e.g. '800 Hz' or an item")],
) -> None:
    _run_return_track_args(
        ctx,
        "return-track device parameter set-display",
        {
            "return_track": return_track,
            "device": device,
            "parameter": parameter,
            "display": display,
        },
        lambda client: client.return_track_device_parameter_set_display(
            return_track, device, parameter, display
        ),
    )


device_app.add_typer(device_parameter_app, name="parameter")
return_track_app.add_typer(name_app, name="name")
return_track_app.add_typer(device_app, name="device")
return_track_app.add_typer(volume_app, name="volume")
return_track_app.add_typer(mute_app, name="mute")
return_track_app.add_typer(solo_app, name="solo")


def register(app: typer.Typer) -> None:
    app.add_typer(return_track_app, name="return-track")
