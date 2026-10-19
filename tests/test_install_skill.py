from __future__ import annotations

from pathlib import Path

import pytest

from ableton_cli.errors import AppError, ExitCode
from ableton_cli.installer import SKILL_DIR_NAME, install_skill


class _PlatformPathsStub:
    def __init__(self, *, claude_home_dir: Path) -> None:
        self._claude_home_dir = claude_home_dir

    def remote_script_candidate_dirs(self) -> list[Path]:
        return []

    def claude_home_dir(self) -> Path:
        return self._claude_home_dir


def _write_source(tmp_path: Path, content: str) -> Path:
    source = tmp_path / "source" / SKILL_DIR_NAME / "SKILL.md"
    source.parent.mkdir(parents=True, exist_ok=True)
    source.write_text(content, encoding="utf-8")
    return source


def test_install_skill_installs_and_updates(monkeypatch, tmp_path: Path) -> None:
    source = _write_source(tmp_path, "name: first")
    claude_home = tmp_path / ".claude"
    platform_paths = _PlatformPathsStub(claude_home_dir=claude_home)
    monkeypatch.setattr("ableton_cli.installer.skill_source_file", lambda: source)

    first = install_skill(dry_run=False, yes=True, platform_paths=platform_paths)
    target = claude_home / "skills" / SKILL_DIR_NAME / "SKILL.md"
    assert first["action"] == "install"
    assert first["home"] == str(claude_home)
    assert target.read_text(encoding="utf-8") == "name: first"

    source.write_text("name: second", encoding="utf-8")
    second = install_skill(dry_run=False, yes=True, platform_paths=platform_paths)
    assert second["action"] == "update"
    assert target.read_text(encoding="utf-8") == "name: second"


def test_install_skill_supports_explicit_claude_home(monkeypatch, tmp_path: Path) -> None:
    source = _write_source(tmp_path, "name: x")
    override = tmp_path / "custom-claude"
    platform_paths = _PlatformPathsStub(claude_home_dir=tmp_path / ".claude")
    monkeypatch.setattr("ableton_cli.installer.skill_source_file", lambda: source)

    result = install_skill(
        dry_run=False, yes=True, platform_paths=platform_paths, claude_home=override
    )

    assert result["target"] == str(override / "skills" / SKILL_DIR_NAME / "SKILL.md")


def test_install_skill_dry_run_writes_nothing(monkeypatch, tmp_path: Path) -> None:
    source = _write_source(tmp_path, "name: x")
    claude_home = tmp_path / ".claude"
    platform_paths = _PlatformPathsStub(claude_home_dir=claude_home)
    monkeypatch.setattr("ableton_cli.installer.skill_source_file", lambda: source)

    result = install_skill(dry_run=True, yes=True, platform_paths=platform_paths)

    assert result["dry_run"] is True
    assert not claude_home.exists()


def test_install_skill_fails_when_source_is_missing(monkeypatch, tmp_path: Path) -> None:
    platform_paths = _PlatformPathsStub(claude_home_dir=tmp_path / ".claude")
    monkeypatch.setattr(
        "ableton_cli.installer.skill_source_file", lambda: tmp_path / "missing" / "SKILL.md"
    )

    with pytest.raises(AppError) as exc_info:
        install_skill(dry_run=False, yes=True, platform_paths=platform_paths)

    assert exc_info.value.exit_code == ExitCode.EXECUTION_FAILED
