from __future__ import annotations

import time as _time
from collections.abc import Callable
from typing import Annotated, Any

import typer

from ..errors import AppError, ErrorCode, ExitCode
from ._arrangement_specs import ArrangementCommandSpec
from ._validation import (
    invalid_argument,
    require_non_empty_string,
    require_non_negative,
    require_non_negative_float,
)

#: Live applies ``Song.current_song_time`` on its next update (display tick, ~100 ms).
PLAYHEAD_POLL_INTERVAL_S = 0.05
PLAYHEAD_WAIT_TIMEOUT_S = 3.0
_PLAYHEAD_TOLERANCE = 1e-6
_LOCATOR_INDEX_HINT = "Use an index from 'arrangement locator list'."

# Injectable for tests.
_sleep: Callable[[float], None] = _time.sleep
_monotonic: Callable[[], float] = _time.monotonic

LOCATOR_LIST_SPEC = ArrangementCommandSpec(
    command_name="arrangement locator list",
    client_method="locators_list",
)

LOCATOR_ADD_SPEC = ArrangementCommandSpec(
    command_name="arrangement locator add",
    client_method="locator_add",
)

LOCATOR_DELETE_SPEC = ArrangementCommandSpec(
    command_name="arrangement locator delete",
    client_method="locator_delete",
)


def _require_stopped_transport(client: Any, action: str) -> None:
    if bool(client.song_info().get("is_playing")):
        raise invalid_argument(
            message=f"Cannot {action} a locator while the transport is playing",
            hint="Stop the transport first ('transport stop').",
        )


def _move_playhead_and_wait(client: Any, beat: float) -> None:
    """Move the playhead and wait until Live reports it there.

    Live applies a playhead move on its next update and toggles cue points only at
    the applied position, so the locator request must wait for it.
    """
    client.transport_position_set(beat)
    deadline = _monotonic() + PLAYHEAD_WAIT_TIMEOUT_S
    while True:
        current = float(client.transport_position_get()["current_time"])
        if abs(current - beat) < _PLAYHEAD_TOLERANCE:
            return
        if _monotonic() >= deadline:
            raise AppError(
                error_code=ErrorCode.TIMEOUT,
                message=(
                    f"Live did not move the playhead to beat {beat} within "
                    f"{PLAYHEAD_WAIT_TIMEOUT_S:g} s (still at beat {current})"
                ),
                hint=(
                    "Check that the beat lies inside the song length and that Live is "
                    "responsive, then retry."
                ),
                exit_code=ExitCode.TIMEOUT,
            )
        _sleep(PLAYHEAD_POLL_INTERVAL_S)


def _locator_time(client: Any, index: int) -> float:
    locators = list(client.locators_list()["locators"])
    if index >= len(locators):
        raise invalid_argument(message=f"locator out of range: {index}", hint=_LOCATOR_INDEX_HINT)
    return float(locators[index]["time"])


def register_commands(
    locator_app: typer.Typer,
    *,
    run_client_command_spec: Callable[..., None],
    run_client_action: Callable[..., None],
) -> None:
    @locator_app.command("list")
    def arrangement_locator_list(ctx: typer.Context) -> None:
        """List Arrangement locators (cue points), sorted by time."""
        run_client_command_spec(ctx, spec=LOCATOR_LIST_SPEC, args={})

    @locator_app.command("add")
    def arrangement_locator_add(
        ctx: typer.Context,
        time: Annotated[float, typer.Argument(help="Position in beats (>= 0)")],
        name: Annotated[str | None, typer.Option("--name", help="Locator name")] = None,
    ) -> None:
        """Add a locator; the transport must be stopped. Moves the playhead to the locator."""

        def _add(client: Any) -> dict[str, object]:
            valid_time = require_non_negative_float(
                "time", time, hint="Use a beat position such as 0 or 64."
            )
            valid_name = (
                None
                if name is None
                else require_non_empty_string("name", name, hint="Pass a non-empty name.")
            )
            _require_stopped_transport(client, "add")
            _move_playhead_and_wait(client, valid_time)
            return client.locator_add(time=valid_time, name=valid_name)

        run_client_action(
            ctx,
            command_name=LOCATOR_ADD_SPEC.command_name,
            args={"time": time, "name": name},
            fn=_add,
        )

    @locator_app.command("delete")
    def arrangement_locator_delete(
        ctx: typer.Context,
        index: Annotated[int, typer.Argument(help="Locator index from 'arrangement locator list'")],
    ) -> None:
        """Delete a locator; the transport must be stopped. Moves the playhead to the locator."""

        def _delete(client: Any) -> dict[str, object]:
            require_non_negative("index", index, hint=_LOCATOR_INDEX_HINT)
            _require_stopped_transport(client, "delete")
            _move_playhead_and_wait(client, _locator_time(client, index))
            return client.locator_delete(index=index)

        run_client_action(
            ctx,
            command_name=LOCATOR_DELETE_SPEC.command_name,
            args={"index": index},
            fn=_delete,
        )
