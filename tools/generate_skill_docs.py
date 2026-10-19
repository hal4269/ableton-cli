from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path

from ableton_cli.actions import STABLE_ACTION_MAPPINGS

REPO_ROOT = Path(__file__).resolve().parents[1]
ACTIONS_DOC = REPO_ROOT / "docs" / "skills" / "skill-actions.md"

_SKILL_SECTION_START = "## Stable action names and mappings\n"
_SKILL_SECTION_END = "\n## Examples\n"
_ACTION_TABLE_START = "| Action | CLI command | Capability |\n| --- | --- | --- |\n"
_ACTION_TABLE_END = "\n## CLI-only commands (not stable actions)\n"


@dataclass(frozen=True, slots=True)
class GeneratedDocument:
    path: Path
    content: str


def _replace_between(
    *,
    text: str,
    start_marker: str,
    end_marker: str,
    replacement: str,
) -> str:
    start_index = text.find(start_marker)
    if start_index == -1:
        raise RuntimeError(f"start marker not found: {start_marker!r}")
    end_index = text.find(end_marker, start_index)
    if end_index == -1:
        raise RuntimeError(f"end marker not found: {end_marker!r}")
    return text[:start_index] + replacement + text[end_index:]


def _render_action_table() -> str:
    lines = [
        "| Action | CLI command | Capability |",
        "| --- | --- | --- |",
    ]
    for mapping in STABLE_ACTION_MAPPINGS:
        lines.append(f"| `{mapping.action}` | `{mapping.command}` | {mapping.capability} |")
    lines.append("")
    return "\n".join(lines)


def generate_documents() -> tuple[GeneratedDocument, ...]:
    actions_text = ACTIONS_DOC.read_text(encoding="utf-8")

    generated_actions = _replace_between(
        text=actions_text,
        start_marker=_ACTION_TABLE_START,
        end_marker=_ACTION_TABLE_END,
        replacement=_render_action_table(),
    )
    return (GeneratedDocument(path=ACTIONS_DOC, content=generated_actions),)


def _write_documents(documents: tuple[GeneratedDocument, ...]) -> None:
    for item in documents:
        item.path.write_text(item.content, encoding="utf-8", newline="\n")


def _diff_paths(documents: tuple[GeneratedDocument, ...]) -> list[Path]:
    changed: list[Path] = []
    for item in documents:
        current = item.path.read_text(encoding="utf-8")
        if current != item.content:
            changed.append(item.path)
    return changed


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Generate skill action docs from source mappings")
    parser.add_argument(
        "--check",
        action="store_true",
        help="Exit with code 1 when generated output differs from tracked files.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    generated = generate_documents()
    changed = _diff_paths(generated)

    if args.check:
        if changed:
            for path in changed:
                print(f"outdated generated file: {path}")
            return 1
        return 0

    _write_documents(generated)
    for path in changed:
        print(f"updated {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
