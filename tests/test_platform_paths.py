from __future__ import annotations

from pathlib import Path

from ableton_cli.platform_paths import PosixPlatformPaths, WindowsPlatformPaths


def test_windows_platform_paths_returns_expected_directories() -> None:
    home = Path("/home/test-user")
    platform_paths = WindowsPlatformPaths(home=home)

    assert platform_paths.remote_script_candidate_dirs() == [
        home / "Documents" / "Ableton" / "User Library" / "Remote Scripts"
    ]
    assert platform_paths.claude_home_dir() == home / ".claude"
    assert platform_paths.cursor_home_dir() == home / ".cursor"


def test_posix_platform_paths_returns_expected_directories() -> None:
    home = Path("/home/test-user")
    platform_paths = PosixPlatformPaths(
        home=home,
        remote_script_relative_dirs=(
            ("Music", "Ableton", "User Library", "Remote Scripts"),
            ("Documents", "Ableton", "User Library", "Remote Scripts"),
        ),
    )

    assert platform_paths.remote_script_candidate_dirs() == [
        home / "Music" / "Ableton" / "User Library" / "Remote Scripts",
        home / "Documents" / "Ableton" / "User Library" / "Remote Scripts",
    ]
    assert platform_paths.claude_home_dir() == home / ".claude"
    assert platform_paths.cursor_home_dir() == home / ".cursor"


def _write_library_cfg(path: Path, project_path: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        "<Ableton><ContentLibrary><UserLibrary><LibraryProject>"
        f'<ProjectName Value="User Library" /><ProjectPath Value="{project_path}" />'
        "</LibraryProject></UserLibrary></ContentLibrary></Ableton>\n",
        encoding="utf-8",
    )


def test_windows_platform_paths_put_the_configured_user_library_first(tmp_path: Path) -> None:
    home = tmp_path / "home"
    preferences = tmp_path / "AppData" / "Ableton"
    redirected = tmp_path / "Sync" / "Documents" / "Ableton"
    _write_library_cfg(preferences / "Live 12.3.6" / "Preferences" / "Library.cfg", str(redirected))
    _write_library_cfg(
        preferences / "Live 12.10.0" / "Preferences" / "Library.cfg",
        str(home / "Documents" / "Ableton"),
    )

    platform_paths = WindowsPlatformPaths(home=home, preferences_root=preferences)

    # Newest Live version first; the default location is not repeated.
    assert platform_paths.remote_script_candidate_dirs() == [
        home / "Documents" / "Ableton" / "User Library" / "Remote Scripts",
        redirected / "User Library" / "Remote Scripts",
    ]


def test_posix_platform_paths_read_library_cfg_without_preferences_subfolder(
    tmp_path: Path,
) -> None:
    home = tmp_path / "home"
    preferences = home / "Library" / "Preferences" / "Ableton"
    custom = tmp_path / "Volumes" / "Audio" / "Ableton"
    _write_library_cfg(preferences / "Live 12.3.6" / "Library.cfg", str(custom))

    platform_paths = PosixPlatformPaths(
        home=home,
        remote_script_relative_dirs=(("Music", "Ableton", "User Library", "Remote Scripts"),),
        preferences_root=preferences,
    )

    assert platform_paths.remote_script_candidate_dirs() == [
        custom / "User Library" / "Remote Scripts",
        home / "Music" / "Ableton" / "User Library" / "Remote Scripts",
    ]


def test_unreadable_library_cfg_fails_explicitly(tmp_path: Path) -> None:
    import pytest

    from ableton_cli.errors import AppError

    preferences = tmp_path / "Ableton"
    broken = preferences / "Live 12.3.6" / "Preferences" / "Library.cfg"
    broken.parent.mkdir(parents=True)
    broken.write_text("<Ableton", encoding="utf-8")

    with pytest.raises(AppError) as exc_info:
        WindowsPlatformPaths(
            home=tmp_path, preferences_root=preferences
        ).remote_script_candidate_dirs()

    assert str(broken) in exc_info.value.message
