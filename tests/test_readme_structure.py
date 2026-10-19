from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
README_DOC = REPO_ROOT / "README.md"


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_readme_documents_skill_install_and_points_to_agent_rules() -> None:
    markdown = _read(README_DOC)
    assert "## Agent skill" in markdown
    assert "ableton-cli install-skill --yes" in markdown
    assert "AGENTS.md" in markdown
