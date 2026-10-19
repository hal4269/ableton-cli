from __future__ import annotations

import re
import xml.etree.ElementTree as ElementTree
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from .errors import AppError, ErrorCode, ExitCode

CLAUDE_HOME_DIR_NAME = ".claude"
REMOTE_SCRIPTS_DIR_NAME = "Remote Scripts"

#: Live keeps one preferences folder per version ("Live 12.3.6"); Library.cfg sits in its
#: "Preferences" subfolder on Windows and directly inside it on macOS.
_LIBRARY_CFG_PATTERNS = ("Live */Preferences/Library.cfg", "Live */Library.cfg")


class PlatformPaths(Protocol):
    def remote_script_candidate_dirs(self) -> list[Path]: ...

    def claude_home_dir(self) -> Path: ...


def _live_version_key(library_cfg: Path) -> tuple[int, ...]:
    version_dir = next(part for part in library_cfg.parts if part.startswith("Live "))
    return tuple(int(number) for number in re.findall(r"\d+", version_dir))


def _user_library_from_cfg(library_cfg: Path) -> Path | None:
    try:
        root = ElementTree.parse(library_cfg).getroot()
    except (ElementTree.ParseError, OSError) as exc:
        raise AppError(
            error_code=ErrorCode.CONFIG_INVALID,
            message=f"Cannot read Ableton Live library settings: {library_cfg}",
            hint="Open Live once so it rewrites Library.cfg, or remove the broken file.",
            exit_code=ExitCode.CONFIG_INVALID,
        ) from exc
    project = root.find("./ContentLibrary/UserLibrary/LibraryProject")
    if project is None:
        return None
    project_path = project.find("ProjectPath")
    project_name = project.find("ProjectName")
    if project_path is None or project_name is None:
        return None
    return Path(project_path.get("Value", "")) / project_name.get("Value", "")


def configured_remote_script_dirs(preferences_root: Path | None) -> list[Path]:
    """Remote Scripts folders of the User Libraries Live is configured to use.

    Read from every installed Live version's Library.cfg, newest version first, so a
    relocated or redirected User Library is found.
    """
    if preferences_root is None or not preferences_root.is_dir():
        return []
    configs = {path for pattern in _LIBRARY_CFG_PATTERNS for path in preferences_root.glob(pattern)}
    found: list[Path] = []
    for library_cfg in sorted(configs, key=_live_version_key, reverse=True):
        user_library = _user_library_from_cfg(library_cfg)
        if user_library is not None:
            found.append(user_library / REMOTE_SCRIPTS_DIR_NAME)
    return found


def _unique(paths: list[Path]) -> list[Path]:
    seen: set[str] = set()
    unique: list[Path] = []
    for path in paths:
        key = str(path).replace("\\", "/").rstrip("/").lower()
        if key not in seen:
            seen.add(key)
            unique.append(path)
    return unique


@dataclass(slots=True, frozen=True)
class WindowsPlatformPaths:
    home: Path
    preferences_root: Path | None = None

    def remote_script_candidate_dirs(self) -> list[Path]:
        default = self.home / "Documents" / "Ableton" / "User Library" / REMOTE_SCRIPTS_DIR_NAME
        return _unique([*configured_remote_script_dirs(self.preferences_root), default])

    def claude_home_dir(self) -> Path:
        return self.home / CLAUDE_HOME_DIR_NAME


@dataclass(slots=True, frozen=True)
class PosixPlatformPaths:
    home: Path
    remote_script_relative_dirs: tuple[tuple[str, ...], ...]
    preferences_root: Path | None = None

    def remote_script_candidate_dirs(self) -> list[Path]:
        defaults = [
            self.home.joinpath(*path_parts) for path_parts in self.remote_script_relative_dirs
        ]
        return _unique([*configured_remote_script_dirs(self.preferences_root), *defaults])

    def claude_home_dir(self) -> Path:
        return self.home / CLAUDE_HOME_DIR_NAME
