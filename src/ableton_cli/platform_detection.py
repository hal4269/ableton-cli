from __future__ import annotations

import os
import platform
from pathlib import Path

from .errors import AppError, ErrorCode, ExitCode
from .platform_paths import PlatformPaths, PosixPlatformPaths, WindowsPlatformPaths


def build_platform_paths_for_current_os() -> PlatformPaths:
    detected_os = platform.system().lower()
    home = Path.home()

    if detected_os == "windows":
        appdata = os.environ.get("APPDATA")
        return WindowsPlatformPaths(
            home=home,
            preferences_root=Path(appdata) / "Ableton" if appdata else None,
        )
    if detected_os == "darwin":
        return PosixPlatformPaths(
            home=home,
            remote_script_relative_dirs=(
                ("Music", "Ableton", "User Library", "Remote Scripts"),
                ("Documents", "Ableton", "User Library", "Remote Scripts"),
            ),
            preferences_root=home / "Library" / "Preferences" / "Ableton",
        )
    if detected_os == "linux":
        return PosixPlatformPaths(
            home=home,
            remote_script_relative_dirs=(("Ableton", "User Library", "Remote Scripts"),),
        )

    raise AppError(
        error_code=ErrorCode.UNSUPPORTED_OS,
        message=f"Unsupported operating system: {detected_os}",
        hint="Use Windows, macOS, or Linux.",
        exit_code=ExitCode.EXECUTION_FAILED,
    )
