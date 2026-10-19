from __future__ import annotations

from collections.abc import Callable
from typing import Annotated

import typer

from ..refs import (
    DeviceIndexOption,
    DeviceNameOption,
    DeviceQueryOption,
    DeviceStableRefOption,
    ParameterIndexOption,
    ParameterKeyOption,
    ParameterNameOption,
    ParameterQueryOption,
    ParameterStableRefOption,
    SelectedDeviceOption,
    SelectedTrackOption,
    TrackIndexOption,
    TrackNameOption,
    TrackQueryOption,
    TrackStableRefOption,
    build_device_ref,
    build_parameter_ref,
    build_track_ref,
)
from ..runtime import execute_command, get_client
from ._client_command_runner import CommandSpec
from ._client_command_runner import run_client_command as run_client_command_shared
from ._client_command_runner import run_client_command_spec as run_client_command_spec_shared
from ._validation import invalid_argument, require_non_empty_string, require_non_negative

device_app = typer.Typer(help="Device commands", no_args_is_help=True)
parameter_app = typer.Typer(help="Device parameter commands", no_args_is_help=True)
chains_app = typer.Typer(help="Rack chain commands", no_args_is_help=True)
macro_app = typer.Typer(help="Rack macro commands", no_args_is_help=True)


DeviceCommandSpec = CommandSpec


DEVICE_PARAMETER_SET_SPEC = DeviceCommandSpec(
    command_name="device parameter set",
    client_method="set_device_parameter",
)
DEVICE_PARAMETER_SET_DISPLAY_SPEC = DeviceCommandSpec(
    command_name="device parameter set-display",
    client_method="set_device_parameter_display",
)


def run_client_command(
    ctx: typer.Context,
    *,
    command_name: str,
    args: dict[str, object],
    fn: Callable[[object], dict[str, object]],
    resolved_args: Callable[[], dict[str, object]] | None = None,
) -> None:
    run_client_command_shared(
        ctx,
        command_name=command_name,
        args=args,
        fn=fn,
        get_client_fn=get_client,
        execute_command_fn=execute_command,
        resolved_args=resolved_args,
    )


def run_client_command_spec(
    ctx: typer.Context,
    *,
    spec: DeviceCommandSpec,
    args: dict[str, object],
    method_kwargs: dict[str, object] | Callable[[], dict[str, object]] | None = None,
    resolved_args: Callable[[], dict[str, object]] | None = None,
) -> None:
    run_client_command_spec_shared(
        ctx,
        spec=spec,
        args=args,
        method_kwargs=method_kwargs,
        get_client_fn=get_client,
        execute_command_fn=execute_command,
        resolved_args=resolved_args,
    )


@parameter_app.command("set-display")
def set_device_parameter_display(
    ctx: typer.Context,
    display: Annotated[
        str,
        typer.Argument(help="Value as Live displays it, e.g. '800 Hz', '120 ms', 'Saw 8'"),
    ],
    track_index: TrackIndexOption = None,
    track_name: TrackNameOption = None,
    selected_track: SelectedTrackOption = False,
    track_query: TrackQueryOption = None,
    track_ref: TrackStableRefOption = None,
    device_index: DeviceIndexOption = None,
    device_name: DeviceNameOption = None,
    selected_device: SelectedDeviceOption = False,
    device_query: DeviceQueryOption = None,
    device_ref: DeviceStableRefOption = None,
    parameter_index: ParameterIndexOption = None,
    parameter_name: ParameterNameOption = None,
    parameter_query: ParameterQueryOption = None,
    parameter_key: ParameterKeyOption = None,
    parameter_ref: ParameterStableRefOption = None,
) -> None:
    """Set a parameter by its display value; the Remote Script finds the raw value."""

    def _method_kwargs() -> dict[str, object]:
        return {
            "track_ref": build_track_ref(
                track_index=track_index,
                track_name=track_name,
                selected_track=selected_track,
                track_query=track_query,
                track_ref=track_ref,
            ),
            "device_ref": build_device_ref(
                device_index=device_index,
                device_name=device_name,
                selected_device=selected_device,
                device_query=device_query,
                device_ref=device_ref,
            ),
            "parameter_ref": build_parameter_ref(
                parameter_index=parameter_index,
                parameter_name=parameter_name,
                parameter_query=parameter_query,
                parameter_key=parameter_key,
                parameter_ref=parameter_ref,
            ),
            "display": require_non_empty_string(
                "display", display, hint="Pass a display value such as '800 Hz'."
            ),
        }

    run_client_command_spec(
        ctx,
        spec=DEVICE_PARAMETER_SET_DISPLAY_SPEC,
        args={"display": display},
        method_kwargs=_method_kwargs,
        resolved_args=_method_kwargs,
    )


@parameter_app.command("set")
def set_device_parameter(
    ctx: typer.Context,
    value: Annotated[float, typer.Argument(help="Target parameter value")],
    track_index: TrackIndexOption = None,
    track_name: TrackNameOption = None,
    selected_track: SelectedTrackOption = False,
    track_query: TrackQueryOption = None,
    track_ref: TrackStableRefOption = None,
    device_index: DeviceIndexOption = None,
    device_name: DeviceNameOption = None,
    selected_device: SelectedDeviceOption = False,
    device_query: DeviceQueryOption = None,
    device_ref: DeviceStableRefOption = None,
    parameter_index: ParameterIndexOption = None,
    parameter_name: ParameterNameOption = None,
    parameter_query: ParameterQueryOption = None,
    parameter_key: ParameterKeyOption = None,
    parameter_ref: ParameterStableRefOption = None,
) -> None:
    def _resolved_refs() -> tuple[dict[str, object], dict[str, object], dict[str, object]]:
        return (
            build_track_ref(
                track_index=track_index,
                track_name=track_name,
                selected_track=selected_track,
                track_query=track_query,
                track_ref=track_ref,
            ),
            build_device_ref(
                device_index=device_index,
                device_name=device_name,
                selected_device=selected_device,
                device_query=device_query,
                device_ref=device_ref,
            ),
            build_parameter_ref(
                parameter_index=parameter_index,
                parameter_name=parameter_name,
                parameter_query=parameter_query,
                parameter_key=parameter_key,
                parameter_ref=parameter_ref,
            ),
        )

    def _method_kwargs() -> dict[str, object]:
        resolved_track_ref, resolved_device_ref, resolved_parameter_ref = _resolved_refs()
        return {
            "track_ref": resolved_track_ref,
            "device_ref": resolved_device_ref,
            "parameter_ref": resolved_parameter_ref,
            "value": value,
        }

    run_client_command_spec(
        ctx,
        spec=DEVICE_PARAMETER_SET_SPEC,
        args={
            "track_ref": None,
            "device_ref": None,
            "parameter_ref": None,
            "value": value,
        },
        method_kwargs=_method_kwargs,
        resolved_args=lambda: {
            "track_ref": _resolved_refs()[0],
            "device_ref": _resolved_refs()[1],
            "parameter_ref": _resolved_refs()[2],
            "value": value,
        },
    )


DEVICE_CHAINS_LIST_SPEC = DeviceCommandSpec(
    command_name="device chains list",
    client_method="device_chains_list",
)

DEVICE_MACRO_LIST_SPEC = DeviceCommandSpec(
    command_name="device macro list",
    client_method="device_macro_list",
)

DEVICE_MACRO_SET_SPEC = DeviceCommandSpec(
    command_name="device macro set",
    client_method="device_macro_set",
)


def _device_target_refs(
    *,
    track_index: int | None,
    track_name: str | None,
    selected_track: bool,
    track_query: str | None,
    track_ref: str | None,
    device_index: int | None,
    device_name: str | None,
    selected_device: bool,
    device_query: str | None,
    device_ref: str | None,
) -> tuple[dict[str, object], dict[str, object]]:
    return (
        build_track_ref(
            track_index=track_index,
            track_name=track_name,
            selected_track=selected_track,
            track_query=track_query,
            track_ref=track_ref,
        ),
        build_device_ref(
            device_index=device_index,
            device_name=device_name,
            selected_device=selected_device,
            device_query=device_query,
            device_ref=device_ref,
        ),
    )


@chains_app.command("list")
def device_chains_list(
    ctx: typer.Context,
    track_index: TrackIndexOption = None,
    track_name: TrackNameOption = None,
    selected_track: SelectedTrackOption = False,
    track_query: TrackQueryOption = None,
    track_ref: TrackStableRefOption = None,
    device_index: DeviceIndexOption = None,
    device_name: DeviceNameOption = None,
    selected_device: SelectedDeviceOption = False,
    device_query: DeviceQueryOption = None,
    device_ref: DeviceStableRefOption = None,
) -> None:
    def _resolved_refs() -> tuple[dict[str, object], dict[str, object]]:
        return _device_target_refs(
            track_index=track_index,
            track_name=track_name,
            selected_track=selected_track,
            track_query=track_query,
            track_ref=track_ref,
            device_index=device_index,
            device_name=device_name,
            selected_device=selected_device,
            device_query=device_query,
            device_ref=device_ref,
        )

    def _method_kwargs() -> dict[str, object]:
        resolved_track_ref, resolved_device_ref = _resolved_refs()
        return {"track_ref": resolved_track_ref, "device_ref": resolved_device_ref}

    run_client_command_spec(
        ctx,
        spec=DEVICE_CHAINS_LIST_SPEC,
        args={"track_ref": None, "device_ref": None},
        method_kwargs=_method_kwargs,
        resolved_args=lambda: {
            "track_ref": _resolved_refs()[0],
            "device_ref": _resolved_refs()[1],
        },
    )


@macro_app.command("list")
def device_macro_list(
    ctx: typer.Context,
    track_index: TrackIndexOption = None,
    track_name: TrackNameOption = None,
    selected_track: SelectedTrackOption = False,
    track_query: TrackQueryOption = None,
    track_ref: TrackStableRefOption = None,
    device_index: DeviceIndexOption = None,
    device_name: DeviceNameOption = None,
    selected_device: SelectedDeviceOption = False,
    device_query: DeviceQueryOption = None,
    device_ref: DeviceStableRefOption = None,
) -> None:
    def _resolved_refs() -> tuple[dict[str, object], dict[str, object]]:
        return _device_target_refs(
            track_index=track_index,
            track_name=track_name,
            selected_track=selected_track,
            track_query=track_query,
            track_ref=track_ref,
            device_index=device_index,
            device_name=device_name,
            selected_device=selected_device,
            device_query=device_query,
            device_ref=device_ref,
        )

    def _method_kwargs() -> dict[str, object]:
        resolved_track_ref, resolved_device_ref = _resolved_refs()
        return {"track_ref": resolved_track_ref, "device_ref": resolved_device_ref}

    run_client_command_spec(
        ctx,
        spec=DEVICE_MACRO_LIST_SPEC,
        args={"track_ref": None, "device_ref": None},
        method_kwargs=_method_kwargs,
        resolved_args=lambda: {
            "track_ref": _resolved_refs()[0],
            "device_ref": _resolved_refs()[1],
        },
    )


@macro_app.command("set")
def device_macro_set(
    ctx: typer.Context,
    macro_index: Annotated[int, typer.Argument(help="Macro index (0-based)")],
    value: Annotated[float, typer.Argument(help="Target macro value")],
    track_index: TrackIndexOption = None,
    track_name: TrackNameOption = None,
    selected_track: SelectedTrackOption = False,
    track_query: TrackQueryOption = None,
    track_ref: TrackStableRefOption = None,
    device_index: DeviceIndexOption = None,
    device_name: DeviceNameOption = None,
    selected_device: SelectedDeviceOption = False,
    device_query: DeviceQueryOption = None,
    device_ref: DeviceStableRefOption = None,
) -> None:
    def _resolved_refs() -> tuple[dict[str, object], dict[str, object]]:
        return _device_target_refs(
            track_index=track_index,
            track_name=track_name,
            selected_track=selected_track,
            track_query=track_query,
            track_ref=track_ref,
            device_index=device_index,
            device_name=device_name,
            selected_device=selected_device,
            device_query=device_query,
            device_ref=device_ref,
        )

    def _method_kwargs() -> dict[str, object]:
        resolved_track_ref, resolved_device_ref = _resolved_refs()
        return {
            "track_ref": resolved_track_ref,
            "device_ref": resolved_device_ref,
            "macro_index": macro_index,
            "value": value,
        }

    run_client_command_spec(
        ctx,
        spec=DEVICE_MACRO_SET_SPEC,
        args={
            "track_ref": None,
            "device_ref": None,
            "macro_index": macro_index,
            "value": value,
        },
        method_kwargs=_method_kwargs,
        resolved_args=lambda: {
            "track_ref": _resolved_refs()[0],
            "device_ref": _resolved_refs()[1],
            "macro_index": macro_index,
            "value": value,
        },
    )


DEVICE_DELETE_SPEC = DeviceCommandSpec(command_name="device delete", client_method="device_delete")
DEVICE_MOVE_SPEC = DeviceCommandSpec(command_name="device move", client_method="device_move")
DEVICE_ENABLED_SET_SPEC = DeviceCommandSpec(
    command_name="device enabled set",
    client_method="device_enabled_set",
)
DEVICE_PARAMETER_LIST_SPEC = DeviceCommandSpec(
    command_name="device parameter list",
    client_method="device_parameters_list",
)

enabled_app = typer.Typer(help="Device on/off commands", no_args_is_help=True)


def _run_device_target_command(
    ctx: typer.Context,
    *,
    spec: DeviceCommandSpec,
    selectors: dict[str, object],
    extra_args: dict[str, object],
    validated_extra: Callable[[], dict[str, object]] | None = None,
) -> None:
    """Run a command on one device picked by the standard track + device selectors.

    ``extra_args`` are echoed in the output envelope; ``validated_extra`` (when
    given) validates them and returns the client kwargs, so validation errors
    are reported through the standard envelope.
    """

    def _refs() -> dict[str, object]:
        track_ref, device_ref = _device_target_refs(**selectors)  # type: ignore[arg-type]
        return {"track_ref": track_ref, "device_ref": device_ref}

    def _extra() -> dict[str, object]:
        return validated_extra() if validated_extra is not None else extra_args

    run_client_command_spec(
        ctx,
        spec=spec,
        args={"track_ref": None, "device_ref": None, **extra_args},
        method_kwargs=lambda: {**_refs(), **_extra()},
        resolved_args=lambda: {**_refs(), **extra_args},
    )


@device_app.command("delete")
def device_delete(
    ctx: typer.Context,
    track_index: TrackIndexOption = None,
    track_name: TrackNameOption = None,
    selected_track: SelectedTrackOption = False,
    track_query: TrackQueryOption = None,
    track_ref: TrackStableRefOption = None,
    device_index: DeviceIndexOption = None,
    device_name: DeviceNameOption = None,
    selected_device: SelectedDeviceOption = False,
    device_query: DeviceQueryOption = None,
    device_ref: DeviceStableRefOption = None,
) -> None:
    """Delete a device (also inside a rack chain, via --device-ref)."""
    selectors = dict(locals())
    selectors.pop("ctx")
    _run_device_target_command(ctx, spec=DEVICE_DELETE_SPEC, selectors=selectors, extra_args={})


@device_app.command("move")
def device_move(
    ctx: typer.Context,
    to_index: Annotated[int, typer.Option("--to-index", help="Destination position (0-based)")],
    track_index: TrackIndexOption = None,
    track_name: TrackNameOption = None,
    selected_track: SelectedTrackOption = False,
    track_query: TrackQueryOption = None,
    track_ref: TrackStableRefOption = None,
    device_index: DeviceIndexOption = None,
    device_name: DeviceNameOption = None,
    selected_device: SelectedDeviceOption = False,
    device_query: DeviceQueryOption = None,
    device_ref: DeviceStableRefOption = None,
) -> None:
    """Move a top-level device to another position on its track."""
    selectors = dict(locals())
    for name in ("ctx", "to_index"):
        selectors.pop(name)
    _run_device_target_command(
        ctx, spec=DEVICE_MOVE_SPEC, selectors=selectors, extra_args={"to_index": to_index}
    )


@enabled_app.command("set")
def device_enabled_set(
    ctx: typer.Context,
    value: Annotated[bool, typer.Argument(help="Device on: true|false", metavar="VALUE")],
    track_index: TrackIndexOption = None,
    track_name: TrackNameOption = None,
    selected_track: SelectedTrackOption = False,
    track_query: TrackQueryOption = None,
    track_ref: TrackStableRefOption = None,
    device_index: DeviceIndexOption = None,
    device_name: DeviceNameOption = None,
    selected_device: SelectedDeviceOption = False,
    device_query: DeviceQueryOption = None,
    device_ref: DeviceStableRefOption = None,
) -> None:
    """Switch a device on or off (its 'Device On' parameter)."""
    selectors = dict(locals())
    for name in ("ctx", "value"):
        selectors.pop(name)
    _run_device_target_command(
        ctx, spec=DEVICE_ENABLED_SET_SPEC, selectors=selectors, extra_args={"value": value}
    )


@parameter_app.command("list")
def device_parameter_list(
    ctx: typer.Context,
    track_index: TrackIndexOption = None,
    track_name: TrackNameOption = None,
    selected_track: SelectedTrackOption = False,
    track_query: TrackQueryOption = None,
    track_ref: TrackStableRefOption = None,
    device_index: DeviceIndexOption = None,
    device_name: DeviceNameOption = None,
    selected_device: SelectedDeviceOption = False,
    device_query: DeviceQueryOption = None,
    device_ref: DeviceStableRefOption = None,
) -> None:
    """List all parameters of a device (also inside a rack chain, via --device-ref)."""
    selectors = dict(locals())
    selectors.pop("ctx")
    _run_device_target_command(
        ctx, spec=DEVICE_PARAMETER_LIST_SPEC, selectors=selectors, extra_args={}
    )


DEVICE_CHAIN_GET_SPEC = DeviceCommandSpec(
    command_name="device chains get", client_method="device_chain_get"
)
DEVICE_CHAIN_SET_SPEC = DeviceCommandSpec(
    command_name="device chains set", client_method="device_chain_set"
)
DEVICE_VARIATIONS_LIST_SPEC = DeviceCommandSpec(
    command_name="device variation list", client_method="device_variations_list"
)
DEVICE_VARIATION_STORE_SPEC = DeviceCommandSpec(
    command_name="device variation store", client_method="device_variation_store"
)
DEVICE_VARIATION_RECALL_SPEC = DeviceCommandSpec(
    command_name="device variation recall", client_method="device_variation_recall"
)
DEVICE_VARIATION_DELETE_SPEC = DeviceCommandSpec(
    command_name="device variation delete", client_method="device_variation_delete"
)
DEVICE_INSERT_SPEC = DeviceCommandSpec(command_name="device insert", client_method="device_insert")

variation_app = typer.Typer(help="Rack macro variation commands", no_args_is_help=True)

#: Drum Rack choke groups: 0 = none, 1-16.
CHOKE_GROUP_MAX = 16

ChainIndexArgument = Annotated[int, typer.Argument(help="Chain index (0-based)")]
VariationIndexArgument = Annotated[int, typer.Argument(help="Variation index (0-based)")]

_CHAIN_HINT = "Use a chain index from 'device chains list'."
_VARIATION_HINT = "Use a variation index from 'device variation list'."


def _index_kwargs(name: str, value: int, hint: str) -> Callable[[], dict[str, object]]:
    return lambda: {name: require_non_negative(name, value, hint=hint)}


@chains_app.command("get")
def device_chain_get(
    ctx: typer.Context,
    chain_index: ChainIndexArgument,
    track_index: TrackIndexOption = None,
    track_name: TrackNameOption = None,
    selected_track: SelectedTrackOption = False,
    track_query: TrackQueryOption = None,
    track_ref: TrackStableRefOption = None,
    device_index: DeviceIndexOption = None,
    device_name: DeviceNameOption = None,
    selected_device: SelectedDeviceOption = False,
    device_query: DeviceQueryOption = None,
    device_ref: DeviceStableRefOption = None,
) -> None:
    """Show a rack chain's volume, panning, mute, solo and choke group."""
    selectors = dict(locals())
    for name in ("ctx", "chain_index"):
        selectors.pop(name)
    _run_device_target_command(
        ctx,
        spec=DEVICE_CHAIN_GET_SPEC,
        selectors=selectors,
        extra_args={"chain_index": chain_index},
        validated_extra=_index_kwargs("chain_index", chain_index, _CHAIN_HINT),
    )


def _chain_settings(
    *,
    volume: float | None,
    panning: float | None,
    mute: bool | None,
    solo: bool | None,
    choke_group: int | None,
) -> dict[str, object]:
    candidates: dict[str, object | None] = {
        "volume": volume,
        "panning": panning,
        "mute": mute,
        "solo": solo,
        "choke_group": choke_group,
    }
    settings = {key: value for key, value in candidates.items() if value is not None}
    if not settings:
        raise invalid_argument(
            message="no chain setting given",
            hint="Pass --volume, --panning, --mute/--no-mute, --solo/--no-solo or --choke-group.",
        )
    if choke_group is not None and not 0 <= choke_group <= CHOKE_GROUP_MAX:
        raise invalid_argument(
            message=f"choke group must be between 0 and {CHOKE_GROUP_MAX}, got {choke_group}",
            hint="Use 0 for no choke group or 1-16.",
        )
    return settings


@chains_app.command("set")
def device_chain_set(
    ctx: typer.Context,
    chain_index: ChainIndexArgument,
    volume: Annotated[
        float | None, typer.Option("--volume", help="Chain volume (0-1, 0.85 = 0 dB)")
    ] = None,
    panning: Annotated[float | None, typer.Option("--panning", help="Chain pan (-1 to 1)")] = None,
    mute: Annotated[bool | None, typer.Option("--mute/--no-mute", help="Chain mute")] = None,
    solo: Annotated[bool | None, typer.Option("--solo/--no-solo", help="Chain solo")] = None,
    choke_group: Annotated[
        int | None,
        typer.Option("--choke-group", help="Drum Rack choke group (0 = none, 1-16)"),
    ] = None,
    track_index: TrackIndexOption = None,
    track_name: TrackNameOption = None,
    selected_track: SelectedTrackOption = False,
    track_query: TrackQueryOption = None,
    track_ref: TrackStableRefOption = None,
    device_index: DeviceIndexOption = None,
    device_name: DeviceNameOption = None,
    selected_device: SelectedDeviceOption = False,
    device_query: DeviceQueryOption = None,
    device_ref: DeviceStableRefOption = None,
) -> None:
    """Change a rack chain's mixer or choke group; only the given options change."""
    selectors = dict(locals())
    settings_args = {
        "volume": volume,
        "panning": panning,
        "mute": mute,
        "solo": solo,
        "choke_group": choke_group,
    }
    for name in ("ctx", "chain_index", *settings_args):
        selectors.pop(name)

    def _validated() -> dict[str, object]:
        require_non_negative("chain_index", chain_index, hint=_CHAIN_HINT)
        return {"chain_index": chain_index, "settings": _chain_settings(**settings_args)}

    _run_device_target_command(
        ctx,
        spec=DEVICE_CHAIN_SET_SPEC,
        selectors=selectors,
        extra_args={"chain_index": chain_index, **settings_args},
        validated_extra=_validated,
    )


@variation_app.command("list")
def device_variations_list(
    ctx: typer.Context,
    track_index: TrackIndexOption = None,
    track_name: TrackNameOption = None,
    selected_track: SelectedTrackOption = False,
    track_query: TrackQueryOption = None,
    track_ref: TrackStableRefOption = None,
    device_index: DeviceIndexOption = None,
    device_name: DeviceNameOption = None,
    selected_device: SelectedDeviceOption = False,
    device_query: DeviceQueryOption = None,
    device_ref: DeviceStableRefOption = None,
) -> None:
    """Show how many macro variations a rack has and which one is selected."""
    selectors = dict(locals())
    selectors.pop("ctx")
    _run_device_target_command(
        ctx, spec=DEVICE_VARIATIONS_LIST_SPEC, selectors=selectors, extra_args={}
    )


@variation_app.command("store")
def device_variation_store(
    ctx: typer.Context,
    track_index: TrackIndexOption = None,
    track_name: TrackNameOption = None,
    selected_track: SelectedTrackOption = False,
    track_query: TrackQueryOption = None,
    track_ref: TrackStableRefOption = None,
    device_index: DeviceIndexOption = None,
    device_name: DeviceNameOption = None,
    selected_device: SelectedDeviceOption = False,
    device_query: DeviceQueryOption = None,
    device_ref: DeviceStableRefOption = None,
) -> None:
    """Store the rack's current macro values as a new variation."""
    selectors = dict(locals())
    selectors.pop("ctx")
    _run_device_target_command(
        ctx, spec=DEVICE_VARIATION_STORE_SPEC, selectors=selectors, extra_args={}
    )


@variation_app.command("recall")
def device_variation_recall(
    ctx: typer.Context,
    variation_index: VariationIndexArgument,
    track_index: TrackIndexOption = None,
    track_name: TrackNameOption = None,
    selected_track: SelectedTrackOption = False,
    track_query: TrackQueryOption = None,
    track_ref: TrackStableRefOption = None,
    device_index: DeviceIndexOption = None,
    device_name: DeviceNameOption = None,
    selected_device: SelectedDeviceOption = False,
    device_query: DeviceQueryOption = None,
    device_ref: DeviceStableRefOption = None,
) -> None:
    """Select a macro variation and recall it (sets the rack's macros)."""
    selectors = dict(locals())
    for name in ("ctx", "variation_index"):
        selectors.pop(name)
    _run_device_target_command(
        ctx,
        spec=DEVICE_VARIATION_RECALL_SPEC,
        selectors=selectors,
        extra_args={"variation_index": variation_index},
        validated_extra=_index_kwargs("variation_index", variation_index, _VARIATION_HINT),
    )


@variation_app.command("delete")
def device_variation_delete(
    ctx: typer.Context,
    variation_index: VariationIndexArgument,
    track_index: TrackIndexOption = None,
    track_name: TrackNameOption = None,
    selected_track: SelectedTrackOption = False,
    track_query: TrackQueryOption = None,
    track_ref: TrackStableRefOption = None,
    device_index: DeviceIndexOption = None,
    device_name: DeviceNameOption = None,
    selected_device: SelectedDeviceOption = False,
    device_query: DeviceQueryOption = None,
    device_ref: DeviceStableRefOption = None,
) -> None:
    """Delete a stored macro variation."""
    selectors = dict(locals())
    for name in ("ctx", "variation_index"):
        selectors.pop(name)
    _run_device_target_command(
        ctx,
        spec=DEVICE_VARIATION_DELETE_SPEC,
        selectors=selectors,
        extra_args={"variation_index": variation_index},
        validated_extra=_index_kwargs("variation_index", variation_index, _VARIATION_HINT),
    )


@device_app.command("insert")
def device_insert(
    ctx: typer.Context,
    device_name: Annotated[
        str,
        typer.Argument(
            metavar="DEVICE_NAME",
            help="Native Live device name as shown in the browser, e.g. 'EQ Eight'",
        ),
    ],
    index: Annotated[
        int | None,
        typer.Option("--index", help="Position in the track's device chain (default: append)"),
    ] = None,
    track_index: TrackIndexOption = None,
    track_name: TrackNameOption = None,
    selected_track: SelectedTrackOption = False,
    track_query: TrackQueryOption = None,
    track_ref: TrackStableRefOption = None,
) -> None:
    """Insert a native Live device at a position on a track (Live 12.1.10+)."""

    def _track_ref() -> dict[str, object]:
        return build_track_ref(
            track_index=track_index,
            track_name=track_name,
            selected_track=selected_track,
            track_query=track_query,
            track_ref=track_ref,
        )

    def _method_kwargs() -> dict[str, object]:
        name = require_non_empty_string(
            "device_name", device_name, hint="Pass a native device name."
        )
        if index is not None:
            require_non_negative("index", index, hint="Use 0 for the first position.")
        return {"track_ref": _track_ref(), "device_name": name, "index": index}

    run_client_command_spec(
        ctx,
        spec=DEVICE_INSERT_SPEC,
        args={"track_ref": None, "device_name": device_name, "index": index},
        method_kwargs=_method_kwargs,
        resolved_args=lambda: {
            "track_ref": _track_ref(),
            "device_name": device_name,
            "index": index,
        },
    )


device_app.add_typer(parameter_app, name="parameter")
device_app.add_typer(chains_app, name="chains")
device_app.add_typer(macro_app, name="macro")
device_app.add_typer(enabled_app, name="enabled")
device_app.add_typer(variation_app, name="variation")


def register(app: typer.Typer) -> None:
    app.add_typer(device_app, name="device")
