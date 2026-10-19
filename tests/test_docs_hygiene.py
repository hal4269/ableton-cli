from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
README_DOC = REPO_ROOT / "README.md"
SKILL_DOC = REPO_ROOT / "skills" / "ableton-cli" / "SKILL.md"
ENVIRONMENT_INDEPENDENT_DOC_GLOBS = (
    "AGENTS.md",
    "README.md",
    "skills/ableton-cli/SKILL.md",
    "docs/skills/**/*.md",
)
UPSTREAM_ACCOUNT = "".join(("6uc", "lz1"))
HOST_SPECIFIC_MARKERS = (UPSTREAM_ACCOUNT, "/" + "Users/")
# The README credits the original author by account name.
UPSTREAM_ATTRIBUTION_DOCS = ("README.md",)


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _environment_independent_docs() -> tuple[Path, ...]:
    paths: set[Path] = set()
    for pattern in ENVIRONMENT_INDEPENDENT_DOC_GLOBS:
        paths.update(path for path in REPO_ROOT.glob(pattern) if path.is_file())
    return tuple(sorted(paths))


def test_agent_docs_do_not_reference_host_specific_paths() -> None:
    violations = [
        f"{path.relative_to(REPO_ROOT)} contains {marker!r}"
        for path in _environment_independent_docs()
        for marker in HOST_SPECIFIC_MARKERS
        if marker in _read(path)
        and not (
            marker == UPSTREAM_ACCOUNT
            and str(path.relative_to(REPO_ROOT)) in UPSTREAM_ATTRIBUTION_DOCS
        )
    ]

    assert violations == []


def test_readme_includes_protocol_section() -> None:
    markdown = _read(README_DOC)
    assert "## Protocol" in markdown


def test_readme_documents_security_model() -> None:
    markdown = _read(README_DOC)
    assert "## Security Model" in markdown
    assert "127.0.0.1 only" in markdown
    assert "no authentication" in markdown
    assert "--read-only" in markdown


def test_no_outdated_live_11_version_floor_references() -> None:
    outdated_marker = "Live 11+"
    scan_globs = (
        "README.md",
        "docs/**/*.md",
        "skills/ableton-cli/SKILL.md",
        "remote_script/**/*.py",
        "src/**/*.py",
    )
    violations = []
    for pattern in scan_globs:
        for path in REPO_ROOT.glob(pattern):
            if not path.is_file() or "__pycache__" in path.parts:
                continue
            if outdated_marker in _read(path):
                violations.append(str(path.relative_to(REPO_ROOT)))

    assert violations == []


def test_composition_docs_use_browser_discovery_before_drum_kit_loading() -> None:
    docs = "\n".join(
        [
            _read(README_DOC),
            _read(SKILL_DOC),
        ]
    )

    assert 'browser search "Drum Rack"' in docs
    assert 'browser search "Kit"' in docs
    assert "browser load-drum-kit 0 rack:drums --kit-uri kit:acoustic" not in docs
