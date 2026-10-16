from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass
from typing import Annotated, Generic, TypeVar, cast

import typer

from ..runtime import execute_command, get_client
from ._client_command_runner import CommandSpec
from ._client_command_runner import run_client_command_spec as run_client_command_spec_shared
from ._validation import (
    invalid_argument,
    require_float_in_range,
    require_scene_and_name,
    require_scene_and_value,
    require_scene_index,
    require_scene_insert_index,
    require_scene_move,
)

scenes_app = typer.Typer(help="Scenes commands", no_args_is_help=True)
name_app = typer.Typer(help="Scenes naming commands", no_args_is_help=True)
tempo_app = typer.Typer(help="Scene tempo (Live 12+)", no_args_is_help=True)
signature_app = typer.Typer(help="Scene time signature (Live 12+)", no_args_is_help=True)

TValue = TypeVar("TValue")

SceneValidator = Callable[[int], int]
SceneValueValidator = Callable[[int, TValue], tuple[int, TValue]]
SceneMoveValidator = Callable[[int, int], tuple[int, int]]

SceneAction = Callable[[object, int], dict[str, object]]
SceneValueAction = Callable[[object, int, TValue], dict[str, object]]
SceneMoveAction = Callable[[object, int, int], dict[str, object]]


@dataclass(frozen=True)
class SceneCommandSpec:
    command_name: str
    client_method: str
    validators: Sequence[SceneValidator] | None = None


@dataclass(frozen=True)
class SceneValueCommandSpec(Generic[TValue]):
    command_name: str
    client_method: str
    value_name: str = "value"
    validators: Sequence[SceneValueValidator[TValue]] | None = None


@dataclass(frozen=True)
class SceneMoveCommandSpec:
    command_name: str
    client_method: str
    validators: Sequence[SceneMoveValidator] | None = None


def run_scene_command(
    ctx: typer.Context,
    *,
    command_name: str,
    scene: int,
    fn: SceneAction,
    validators: Sequence[SceneValidator] | None = None,
) -> None:
    active_validators = validators if validators is not None else (require_scene_index,)

    def _run() -> dict[str, object]:
        valid_scene = scene
        for validator in active_validators:
            valid_scene = validator(valid_scene)
        client = get_client(ctx)
        return fn(client, valid_scene)

    execute_command(
        ctx,
        command=command_name,
        args={"scene": scene},
        action=_run,
    )


def run_scene_value_command(
    ctx: typer.Context,
    *,
    command_name: str,
    scene: int,
    value: TValue,
    fn: SceneValueAction[TValue],
    value_name: str = "value",
    validators: Sequence[SceneValueValidator[TValue]] | None = None,
) -> None:
    active_validators = validators if validators is not None else (require_scene_and_value,)

    def _run() -> dict[str, object]:
        valid_scene = scene
        valid_value = value
        for validator in active_validators:
            valid_scene, valid_value = validator(valid_scene, valid_value)
        client = get_client(ctx)
        return fn(client, valid_scene, valid_value)

    execute_command(
        ctx,
        command=command_name,
        args={"scene": scene, value_name: value},
        action=_run,
    )


def run_scene_move_command(
    ctx: typer.Context,
    *,
    command_name: str,
    from_scene: int,
    to_scene: int,
    fn: SceneMoveAction,
    validators: Sequence[SceneMoveValidator] | None = None,
) -> None:
    active_validators = validators if validators is not None else (require_scene_move,)

    def _run() -> dict[str, object]:
        valid_from_scene = from_scene
        valid_to_scene = to_scene
        for validator in active_validators:
            valid_from_scene, valid_to_scene = validator(valid_from_scene, valid_to_scene)
        client = get_client(ctx)
        return fn(client, valid_from_scene, valid_to_scene)

    execute_command(
        ctx,
        command=command_name,
        args={"from": from_scene, "to": to_scene},
        action=_run,
    )


def run_scene_command_spec(
    ctx: typer.Context,
    *,
    spec: SceneCommandSpec,
    scene: int,
) -> None:
    run_scene_command(
        ctx,
        command_name=spec.command_name,
        scene=scene,
        validators=spec.validators,
        fn=lambda client, valid_scene: cast(
            dict[str, object],
            getattr(client, spec.client_method)(valid_scene),
        ),
    )


def run_scene_value_command_spec(
    ctx: typer.Context,
    *,
    spec: SceneValueCommandSpec[TValue],
    scene: int,
    value: TValue,
) -> None:
    run_scene_value_command(
        ctx,
        command_name=spec.command_name,
        scene=scene,
        value=value,
        value_name=spec.value_name,
        validators=spec.validators,
        fn=lambda client, valid_scene, valid_value: cast(
            dict[str, object],
            getattr(client, spec.client_method)(valid_scene, valid_value),
        ),
    )


def run_scene_move_command_spec(
    ctx: typer.Context,
    *,
    spec: SceneMoveCommandSpec,
    from_scene: int,
    to_scene: int,
) -> None:
    run_scene_move_command(
        ctx,
        command_name=spec.command_name,
        from_scene=from_scene,
        to_scene=to_scene,
        validators=spec.validators,
        fn=lambda client, valid_from_scene, valid_to_scene: cast(
            dict[str, object],
            getattr(client, spec.client_method)(valid_from_scene, valid_to_scene),
        ),
    )


SCENE_NAME_SET_SPEC = SceneValueCommandSpec[str](
    command_name="scenes name set",
    client_method="set_scene_name",
    value_name="name",
    validators=(require_scene_and_name,),
)

SCENE_FIRE_SPEC = SceneCommandSpec(
    command_name="scenes fire",
    client_method="fire_scene",
)

SCENE_DUPLICATE_SPEC = SceneCommandSpec(
    command_name="scenes duplicate",
    client_method="scenes_duplicate",
)

SCENE_DELETE_SPEC = SceneCommandSpec(
    command_name="scenes delete",
    client_method="scenes_delete",
)

SCENE_MOVE_SPEC = SceneMoveCommandSpec(
    command_name="scenes move",
    client_method="scenes_move",
)


@scenes_app.command("list")
def scenes_list(ctx: typer.Context) -> None:
    def _run() -> dict[str, object]:
        client = get_client(ctx)
        return client.scenes_list()

    execute_command(
        ctx,
        command="scenes list",
        args={},
        action=_run,
    )


@scenes_app.command("create")
def scenes_create(
    ctx: typer.Context,
    index: Annotated[
        int,
        typer.Option(
            "--index",
            help="Insert index (-1 for append)",
        ),
    ] = -1,
) -> None:
    def _run() -> dict[str, object]:
        valid_index = require_scene_insert_index(index)
        client = get_client(ctx)
        return client.create_scene(valid_index)

    execute_command(
        ctx,
        command="scenes create",
        args={"index": index},
        action=_run,
    )


@name_app.command("set")
def scenes_name_set(
    ctx: typer.Context,
    scene: Annotated[int, typer.Argument(help="Scene index (0-based)")],
    name: Annotated[str, typer.Argument(help="New scene name")],
) -> None:
    run_scene_value_command_spec(
        ctx,
        spec=SCENE_NAME_SET_SPEC,
        scene=scene,
        value=name,
    )


@scenes_app.command("fire")
def scenes_fire(
    ctx: typer.Context,
    scene: Annotated[int, typer.Argument(help="Scene index (0-based)")],
) -> None:
    run_scene_command_spec(
        ctx,
        spec=SCENE_FIRE_SPEC,
        scene=scene,
    )


@scenes_app.command("move")
def scenes_move(
    ctx: typer.Context,
    from_scene: Annotated[int, typer.Argument(help="Source scene index (0-based)")],
    to_scene: Annotated[int, typer.Argument(help="Destination scene index (0-based)")],
) -> None:
    run_scene_move_command_spec(
        ctx,
        spec=SCENE_MOVE_SPEC,
        from_scene=from_scene,
        to_scene=to_scene,
    )


@scenes_app.command("duplicate")
def scenes_duplicate(
    ctx: typer.Context,
    scene: Annotated[int, typer.Argument(help="Scene index (0-based)")],
) -> None:
    """Duplicate a scene with its clips; the copy lands right after it."""
    run_scene_command_spec(ctx, spec=SCENE_DUPLICATE_SPEC, scene=scene)


@scenes_app.command("delete")
def scenes_delete(
    ctx: typer.Context,
    scene: Annotated[int, typer.Argument(help="Scene index (0-based)")],
) -> None:
    """Delete a scene and its clips."""
    run_scene_command_spec(ctx, spec=SCENE_DELETE_SPEC, scene=scene)


SCENE_TEMPO_SET_SPEC = CommandSpec(command_name="scenes tempo set", client_method="scene_tempo_set")
SCENE_SIGNATURE_SET_SPEC = CommandSpec(
    command_name="scenes signature set", client_method="scene_signature_set"
)

#: Live's tempo range (bpm).
_MIN_BPM = 20.0
_MAX_BPM = 999.0
_SIGNATURE_DENOMINATORS = (1, 2, 4, 8, 16)


def _run_spec(
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


@tempo_app.command("set")
def scenes_tempo_set(
    ctx: typer.Context,
    scene: Annotated[int, typer.Argument(help="Scene index (0-based)")],
    bpm: Annotated[float | None, typer.Argument(help="Tempo the scene sets when launched")] = None,
    clear: Annotated[bool, typer.Option("--clear", help="Remove the scene's tempo")] = False,
) -> None:
    """Give a scene its own tempo, or --clear it (Scene.tempo / tempo_enabled)."""

    def _method_kwargs() -> dict[str, object]:
        require_scene_index(scene)
        if (bpm is None) == (not clear):
            raise invalid_argument(
                message="pass either a tempo or --clear",
                hint="Example: 'scenes tempo set 1 128' or 'scenes tempo set 1 --clear'.",
            )
        valid_bpm = None
        if bpm is not None:
            valid_bpm = require_float_in_range(
                "bpm", bpm, minimum=_MIN_BPM, maximum=_MAX_BPM, hint="Use a tempo like 128."
            )
        return {"scene": scene, "bpm": valid_bpm}

    _run_spec(
        ctx,
        spec=SCENE_TEMPO_SET_SPEC,
        args={"scene": scene, "bpm": bpm, "clear": clear},
        method_kwargs=_method_kwargs,
    )


@signature_app.command("set")
def scenes_signature_set(
    ctx: typer.Context,
    scene: Annotated[int, typer.Argument(help="Scene index (0-based)")],
    numerator: Annotated[int | None, typer.Argument(help="Beats per bar (1-99)")] = None,
    denominator: Annotated[int | None, typer.Argument(help="Note value: 1, 2, 4, 8 or 16")] = None,
    clear: Annotated[
        bool, typer.Option("--clear", help="Remove the scene's time signature")
    ] = False,
) -> None:
    """Give a scene its own time signature, or --clear it."""

    def _method_kwargs() -> dict[str, object]:
        require_scene_index(scene)
        if clear:
            if numerator is not None or denominator is not None:
                raise invalid_argument(
                    message="pass either a time signature or --clear",
                    hint="Example: 'scenes signature set 0 7 8' or '... set 0 --clear'.",
                )
            return {"scene": scene, "numerator": None, "denominator": None}
        if (
            numerator is None
            or denominator is None
            or not 1 <= numerator <= 99
            or denominator not in _SIGNATURE_DENOMINATORS
        ):
            raise invalid_argument(
                message=f"invalid time signature {numerator}/{denominator}",
                hint="Use a numerator 1-99 and a denominator of 1, 2, 4, 8 or 16 (e.g. 7 8).",
            )
        return {"scene": scene, "numerator": numerator, "denominator": denominator}

    _run_spec(
        ctx,
        spec=SCENE_SIGNATURE_SET_SPEC,
        args={"scene": scene, "numerator": numerator, "denominator": denominator, "clear": clear},
        method_kwargs=_method_kwargs,
    )


scenes_app.add_typer(name_app, name="name")
scenes_app.add_typer(tempo_app, name="tempo")
scenes_app.add_typer(signature_app, name="signature")


def register(app: typer.Typer) -> None:
    app.add_typer(scenes_app, name="scenes")
