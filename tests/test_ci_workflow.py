from __future__ import annotations

from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
CI_WORKFLOW_PATH = REPO_ROOT / ".github" / "workflows" / "ci.yml"


def _load_ci_workflow() -> dict[str, object]:
    return yaml.safe_load(CI_WORKFLOW_PATH.read_text(encoding="utf-8"))


def test_ci_workflow_limits_default_token_permissions() -> None:
    workflow = _load_ci_workflow()

    assert workflow["permissions"] == {"contents": "read"}


def test_ci_workflow_verifies_generated_files_and_runs_dev_checks() -> None:
    steps = _load_ci_workflow()["jobs"]["test"]["steps"]

    verify = next(step for step in steps if step.get("name") == "Verify generated files")
    assert "python tools/generate_skill_docs.py" in verify["run"]
    assert "python tools/generate_client_methods.py" in verify["run"]
    assert "git diff --exit-code" in verify["run"]

    run_checks = next(step for step in steps if step.get("name") == "Run lint and tests")
    assert run_checks["run"] == "uv run python -m ableton_cli.dev_checks"
