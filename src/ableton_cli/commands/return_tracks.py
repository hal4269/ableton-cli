from __future__ import annotations

from collections.abc import Callable
from typing import Annotated

import typer

from ..runtime import execute_command, get_client
from ._client_command_runner import CommandSpec
from ._client_command_runner import run_client_command_spec as run_client_command_spec_shared
from ._validation import require_non_negative

return_tracks_app = typer.Typer(help="Return track collection commands", no_args_is_help=True)

RETURN_TRACKS_LIST_SPEC = CommandSpec(
    command_name="return-tracks list",
    client_method="return_tracks_list",
)


RETURN_TRACKS_CREATE_SPEC = CommandSpec(
    command_name="return-tracks create",
    client_method="return_tracks_create",
)

RETURN_TRACKS_DELETE_SPEC = CommandSpec(
    command_name="return-tracks delete",
    client_method="return_tracks_delete",
)


def run_client_command_spec(
    ctx: typer.Context,
    *,
    spec: CommandSpec,
    args: dict[str, object],
    method_kwargs: Callable[[], dict[str, object]] | None = None,
) -> None:
    run_client_command_spec_shared(
        ctx,
        spec=spec,
        args=args,
        method_kwargs=method_kwargs,
        get_client_fn=get_client,
        execute_command_fn=execute_command,
    )


@return_tracks_app.command("list")
def return_tracks_list(ctx: typer.Context) -> None:
    run_client_command_spec(
        ctx,
        spec=RETURN_TRACKS_LIST_SPEC,
        args={},
    )


@return_tracks_app.command("create")
def return_tracks_create(ctx: typer.Context) -> None:
    """Add a return track at the end."""
    run_client_command_spec(ctx, spec=RETURN_TRACKS_CREATE_SPEC, args={})


@return_tracks_app.command("delete")
def return_tracks_delete(
    ctx: typer.Context,
    index: Annotated[int, typer.Argument(help="Return track index (0-based)")],
) -> None:
    """Delete a return track."""

    def _method_kwargs() -> dict[str, object]:
        require_non_negative("index", index, hint="Use an index from 'return-tracks list'.")
        return {"index": index}

    run_client_command_spec(
        ctx, spec=RETURN_TRACKS_DELETE_SPEC, args={"index": index}, method_kwargs=_method_kwargs
    )


def register(app: typer.Typer) -> None:
    app.add_typer(return_tracks_app, name="return-tracks")
