from __future__ import annotations

from collections.abc import Callable
from typing import Annotated

import typer

from ._arrangement_specs import ArrangementCommandSpec
from ._validation import require_non_empty_string, require_non_negative, require_non_negative_float

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


def register_commands(
    locator_app: typer.Typer,
    *,
    run_client_command_spec: Callable[..., None],
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
        """Add a locator; the transport must be stopped."""

        def _method_kwargs() -> dict[str, object]:
            valid_time = require_non_negative_float(
                "time", time, hint="Use a beat position such as 0 or 64."
            )
            valid_name = (
                None
                if name is None
                else require_non_empty_string("name", name, hint="Pass a non-empty name.")
            )
            return {"time": valid_time, "name": valid_name}

        run_client_command_spec(
            ctx,
            spec=LOCATOR_ADD_SPEC,
            args={"time": time, "name": name},
            method_kwargs=_method_kwargs,
        )

    @locator_app.command("delete")
    def arrangement_locator_delete(
        ctx: typer.Context,
        index: Annotated[int, typer.Argument(help="Locator index from 'arrangement locator list'")],
    ) -> None:
        """Delete a locator; the transport must be stopped."""

        def _method_kwargs() -> dict[str, object]:
            require_non_negative(
                "index", index, hint="Use an index from 'arrangement locator list'."
            )
            return {"index": index}

        run_client_command_spec(
            ctx,
            spec=LOCATOR_DELETE_SPEC,
            args={"index": index},
            method_kwargs=_method_kwargs,
        )
