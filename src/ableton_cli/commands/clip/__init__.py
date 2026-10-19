from __future__ import annotations

import typer

from ...runtime import execute_command
from ...runtime import get_client as _runtime_get_client
from .._client_command_runner import run_client_command_spec as run_client_command_spec_shared
from ._active_commands import register_active_commands
from ._clip_root_commands import register_clip_root_commands
from ._edit_commands import register_edit_commands
from ._envelope_commands import register_envelope_commands
from ._envelope_mixer_commands import register_envelope_mixer_commands
from ._groove_commands import register_groove_commands
from ._launch_commands import register_launch_commands
from ._name_commands import register_name_commands
from ._notes_commands import register_notes_commands
from ._props_commands import register_prop_commands
from ._theory_commands import register_theory_commands

clip_app = typer.Typer(help="Clip commands", no_args_is_help=True)
notes_app = typer.Typer(help="Clip note commands", no_args_is_help=True)
envelope_app = typer.Typer(help="Clip automation envelope commands", no_args_is_help=True)
envelope_mixer_app = typer.Typer(
    help="Clip envelopes for the track mixer (volume, panning, sends)", no_args_is_help=True
)
name_app = typer.Typer(help="Clip naming commands", no_args_is_help=True)
active_app = typer.Typer(help="Clip active-state commands", no_args_is_help=True)
groove_app = typer.Typer(help="Clip groove commands", no_args_is_help=True)
groove_amount_app = typer.Typer(help="Clip groove amount commands", no_args_is_help=True)
props_app = typer.Typer(help="Clip property commands", no_args_is_help=True)
loop_app = typer.Typer(help="Clip loop commands", no_args_is_help=True)
marker_app = typer.Typer(help="Clip marker commands", no_args_is_help=True)
warp_app = typer.Typer(help="Clip warp commands", no_args_is_help=True)
warp_marker_app = typer.Typer(help="Clip warp marker commands", no_args_is_help=True)
gain_app = typer.Typer(help="Clip gain commands", no_args_is_help=True)
transpose_app = typer.Typer(help="Clip transpose commands", no_args_is_help=True)
file_app = typer.Typer(help="Clip file commands", no_args_is_help=True)
color_app = typer.Typer(help="Clip color commands", no_args_is_help=True)
launch_app = typer.Typer(help="Clip launch setting commands", no_args_is_help=True)
signature_app = typer.Typer(help="Clip time signature commands", no_args_is_help=True)


def get_client(ctx: typer.Context):  # noqa: ANN201
    return _runtime_get_client(ctx)


def run_client_command_spec(ctx: typer.Context, **kwargs: object) -> None:
    run_client_command_spec_shared(
        ctx,
        get_client_fn=get_client,
        execute_command_fn=execute_command,
        **kwargs,
    )


register_notes_commands(notes_app)
register_theory_commands(notes_app)
register_envelope_commands(envelope_app)
register_envelope_mixer_commands(envelope_mixer_app)
register_name_commands(name_app)
register_active_commands(active_app)
register_launch_commands(color_app, launch_app)
register_groove_commands(groove_app, groove_amount_app)
register_clip_root_commands(clip_app)
register_edit_commands(clip_app, signature_app)
register_prop_commands(
    props_app=props_app,
    loop_app=loop_app,
    marker_app=marker_app,
    warp_app=warp_app,
    warp_marker_app=warp_marker_app,
    gain_app=gain_app,
    transpose_app=transpose_app,
    file_app=file_app,
    run_client_command_spec=run_client_command_spec,
)


clip_app.add_typer(notes_app, name="notes")
envelope_app.add_typer(envelope_mixer_app, name="mixer")
clip_app.add_typer(envelope_app, name="envelope")
clip_app.add_typer(name_app, name="name")
clip_app.add_typer(active_app, name="active")
clip_app.add_typer(props_app, name="props")
clip_app.add_typer(loop_app, name="loop")
clip_app.add_typer(marker_app, name="marker")
clip_app.add_typer(warp_app, name="warp")
clip_app.add_typer(warp_marker_app, name="warp-marker")
clip_app.add_typer(gain_app, name="gain")
clip_app.add_typer(transpose_app, name="transpose")
clip_app.add_typer(file_app, name="file")
clip_app.add_typer(color_app, name="color")
clip_app.add_typer(launch_app, name="launch")
clip_app.add_typer(signature_app, name="signature")
groove_app.add_typer(groove_amount_app, name="amount")
clip_app.add_typer(groove_app, name="groove")


def register(app: typer.Typer) -> None:
    app.add_typer(clip_app, name="clip")
