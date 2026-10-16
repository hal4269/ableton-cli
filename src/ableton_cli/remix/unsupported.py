"""Remix operations that have no working implementation.

These commands used to append a hardcoded ``steps`` list to the manifest's
``generated_assets`` and return ``ok: true``. Nothing executed those steps
and nothing read them back, so the only observable effect was an agent
concluding the mix had been set up. Each operation now fails with
``NOT_IMPLEMENTED`` and points at the commands that do work.

Reinstating one means replacing its entry here with a real implementation
plus a remote command that can carry it out — not deleting the entry.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, NoReturn

from ..errors import AppError, not_implemented


@dataclass(frozen=True, slots=True)
class UnsupportedOperation:
    reason: str
    hint: str


UNSUPPORTED_OPERATIONS: dict[str, UnsupportedOperation] = {
    "remix setup-sound": UnsupportedOperation(
        reason="instrument selection needs browser targets discovered at run time",
        hint=(
            "Use 'browser search' to find kit/bass/lead targets, then "
            "'browser load-drum-kit' or 'browser load' with the returned uri."
        ),
    ),
    "remix mix-macro": UnsupportedOperation(
        reason="the Live API cannot create group tracks",
        hint=(
            "Group the buses in Live, add returns with 'return-tracks create', then set "
            "levels with 'track volume set', 'track send set' and 'return-track volume set'."
        ),
    ),
    "remix setup-mix": UnsupportedOperation(
        reason="the Live API cannot create group tracks",
        hint=(
            "Group the buses in Live, add returns with 'return-tracks create', then set "
            "levels with 'track volume set', 'track send set' and 'return-track volume set'."
        ),
    ),
    "remix setup-returns": UnsupportedOperation(
        reason="there is no return-bus plan to apply; returns are created one at a time",
        hint=(
            "Add returns with 'return-tracks create', load effects with 'browser load', "
            "and set levels with 'return-track volume set'."
        ),
    ),
    "remix setup-sidechain": UnsupportedOperation(
        reason="sidechain routing is not exposed to Remote Scripts",
        hint=(
            "Route the sidechain in Live's compressor, then automate it with "
            "'device parameter set' or 'clip envelope set'."
        ),
    ),
    "remix device-chain apply": UnsupportedOperation(
        reason="device chains need browser targets discovered at run time",
        hint=(
            "Use 'browser search' to find each device, then 'browser load' with "
            "the returned uri, and 'device parameter set' to dial it in."
        ),
    ),
    "audio stems split": UnsupportedOperation(
        reason="no stem separation engine ships with this CLI",
        hint=(
            "Separate stems with an external tool, then register the files with "
            "'audio asset add' and read them back with 'audio stems list'."
        ),
    ),
}


def unsupported_help(operation: str) -> str:
    """Help text for a command that always fails: says so, why, and what to use."""
    entry = UNSUPPORTED_OPERATIONS[operation]
    return f"Not supported (always fails): {entry.reason}. {entry.hint}"


def unsupported_error(operation: str, **details: Any) -> AppError:
    entry = UNSUPPORTED_OPERATIONS[operation]
    return not_implemented(
        message=f"{operation} is not implemented: {entry.reason}",
        hint=entry.hint,
        operation=operation,
        **details,
    )


def fail_unsupported(operation: str, **details: Any) -> NoReturn:
    raise unsupported_error(operation, **details)
