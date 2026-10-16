from __future__ import annotations

from collections.abc import Callable
from typing import Annotated

import typer

from ..runtime import execute_command, get_client
from ..song_settings_names import VIEW_NAMES
from ._client_command_runner import CommandSpec
from ._client_command_runner import run_client_command_spec as run_client_command_spec_shared
from ._validation import (
    require_choice,
    require_non_negative,
    require_scene_index,
    require_track_index,
)

view_app = typer.Typer(help="Live's views and selection", no_args_is_help=True)
select_app = typer.Typer(help="Select a track, scene or clip slot", no_args_is_help=True)

VIEW_SHOW_SPEC = CommandSpec(command_name="view show", client_method="view_show")
VIEW_SELECT_TRACK_SPEC = CommandSpec(
    command_name="view select track", client_method="view_select_track"
)
VIEW_SELECT_SCENE_SPEC = CommandSpec(
    command_name="view select scene", client_method="view_select_scene"
)
VIEW_SELECT_CLIP_SPEC = CommandSpec(
    command_name="view select clip", client_method="view_select_clip"
)


def run_client_command_spec(
    ctx: typer.Context,
    *,
    spec: CommandSpec,
    args: dict[str, object],
    method_kwargs: Callable[[], dict[str, object]],
) -> None:
    run_client_command_spec_shared(
        ctx,
        spec=spec,
        args=args,
        method_kwargs=method_kwargs,
        get_client_fn=get_client,
        execute_command_fn=execute_command,
    )


@view_app.command("show")
def view_show(
    ctx: typer.Context,
    view: Annotated[str, typer.Argument(help=f"One of: {', '.join(VIEW_NAMES)}")],
) -> None:
    """Show and focus a view: session, arranger, detail, clip (Detail/Clip) or
    device-chain (Detail/DeviceChain)."""
    run_client_command_spec(
        ctx,
        spec=VIEW_SHOW_SPEC,
        args={"view": view},
        method_kwargs=lambda: {"view": require_choice("view", view, VIEW_NAMES)},
    )


@select_app.command("track")
def view_select_track(
    ctx: typer.Context,
    track: Annotated[int, typer.Argument(help="Track index (0-based)")],
) -> None:
    """Select a track (Song.View.selected_track)."""
    run_client_command_spec(
        ctx,
        spec=VIEW_SELECT_TRACK_SPEC,
        args={"track": track},
        method_kwargs=lambda: {"track": require_track_index(track)},
    )


@select_app.command("scene")
def view_select_scene(
    ctx: typer.Context,
    scene: Annotated[int, typer.Argument(help="Scene index (0-based)")],
) -> None:
    """Select a scene (Song.View.selected_scene)."""
    run_client_command_spec(
        ctx,
        spec=VIEW_SELECT_SCENE_SPEC,
        args={"scene": scene},
        method_kwargs=lambda: {"scene": require_scene_index(scene)},
    )


@select_app.command("clip")
def view_select_clip(
    ctx: typer.Context,
    track: Annotated[int, typer.Argument(help="Track index (0-based)")],
    clip: Annotated[int, typer.Argument(help="Clip slot index (0-based)")],
) -> None:
    """Highlight a clip slot; a clip in it is also shown in the Detail view."""
    run_client_command_spec(
        ctx,
        spec=VIEW_SELECT_CLIP_SPEC,
        args={"track": track, "clip": clip},
        method_kwargs=lambda: {
            "track": require_track_index(track),
            "clip": require_non_negative("clip", clip, hint="Use a clip slot index >= 0."),
        },
    )


view_app.add_typer(select_app, name="select")


def register(app: typer.Typer) -> None:
    app.add_typer(view_app, name="view")
