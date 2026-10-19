from __future__ import annotations

import json
from collections.abc import Callable
from typing import Annotated

import typer

from ..client.events import EventStream
from ..runtime import execute_command, get_client, get_runtime
from ._client_command_runner import CommandSpec
from ._client_command_runner import run_client_command as run_client_command_shared
from ._client_command_runner import run_client_command_spec as run_client_command_spec_shared
from ._validation import (
    invalid_argument,
)

session_app = typer.Typer(help="Session information commands", no_args_is_help=True)


SessionCommandSpec = CommandSpec


SESSION_INFO_SPEC = SessionCommandSpec(
    command_name="session info",
    client_method="get_session_info",
)
SESSION_STOP_ALL_CLIPS_SPEC = SessionCommandSpec(
    command_name="session stop-all-clips",
    client_method="stop_all_clips",
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
    spec: SessionCommandSpec,
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


@session_app.command("info")
def session_info(ctx: typer.Context) -> None:
    run_client_command_spec(
        ctx,
        spec=SESSION_INFO_SPEC,
        args={},
    )


KNOWN_EVENTS: tuple[str, ...] = (
    "tempo",
    "is_playing",
    "playing_position",
    "selected_track",
)


def _validate_events(events: str | None) -> list[str]:
    if events is None:
        return []
    names = [item.strip() for item in events.split(",") if item.strip()]
    unknown = [name for name in names if name not in KNOWN_EVENTS]
    if unknown:
        raise invalid_argument(
            message=f"unknown events: {sorted(unknown)}",
            hint=f"Use --events with any of: {', '.join(KNOWN_EVENTS)}.",
        )
    return names


def _open_event_stream(ctx: typer.Context, **kwargs: object) -> EventStream:
    """Seam for tests: a stream over the resolved runtime settings."""
    return EventStream(get_runtime(ctx).settings, **kwargs)  # type: ignore[arg-type]


@session_app.command("events")
def session_events(
    ctx: typer.Context,
    events: Annotated[
        str | None,
        typer.Option("--events", help=f"Comma-separated subset of: {', '.join(KNOWN_EVENTS)}"),
    ] = None,
    count: Annotated[
        int | None,
        typer.Option("--count", help="Stop after N events (unlimited if omitted)"),
    ] = None,
    idle_timeout_ms: Annotated[
        int | None,
        typer.Option("--idle-timeout-ms", help="Stop after this long with no event"),
    ] = None,
) -> None:
    """Stream events pushed by Live instead of polling for diffs."""
    args = {"events": events, "count": count, "idle_timeout_ms": idle_timeout_ms}

    def _validate() -> dict[str, object]:
        _validate_events(events)
        return {}

    runtime = get_runtime(ctx)
    if (
        runtime.plan
        or runtime.dry_run
        or (runtime.require_confirmation and not runtime.confirm_destructive)
    ):
        execute_command(ctx, command="session events", args=args, action=_validate)
        return

    if events is not None and any(
        name.strip() and name.strip() not in KNOWN_EVENTS for name in events.split(",")
    ):
        execute_command(ctx, command="session events", args=args, action=_validate)
        return

    selected = _validate_events(events)
    stream = _open_event_stream(ctx, events=selected, idle_timeout_ms=idle_timeout_ms)
    try:
        stream.open()
        for event in stream.events(count=count):
            typer.echo(json.dumps(event))
    except KeyboardInterrupt:
        raise typer.Exit(code=0) from None
    finally:
        stream.close()


@session_app.command("stop-all-clips")
def session_stop_all_clips(ctx: typer.Context) -> None:
    run_client_command_spec(
        ctx,
        spec=SESSION_STOP_ALL_CLIPS_SPEC,
        args={},
    )


def register(app: typer.Typer) -> None:
    app.add_typer(session_app, name="session")
