# AGENTS.md

Rules for coding agents (and humans) working on `ableton-cli`: a Python CLI that controls
Ableton Live through a local Remote Script. Deterministic behavior, stable JSON output, fixed
exit codes and explicit failures are part of the product.

## Principles

- **TDD:** red -> green -> refactor for behavioral changes.
- **DRY:** do not duplicate command logic, validation, tests, fixtures or docs.
- **No silent degradation:** fail explicitly with the right error code and hint.
- **No fallbacks or compatibility shims:** no alternate paths, deprecated aliases or
  best-effort branches that hide a missing prerequisite. If a public contract changes, update
  the contract artifacts instead of keeping both behaviors.

## Repository map

- `src/ableton_cli/command_registry.py`: one row per public command (name, remote command,
  side effect) and the client method specs. Adding a command starts here.
- `src/ableton_cli/commands/`: Typer commands. `src/ableton_cli/client/`: TCP client
  (`_client_generated.py` is generated).
- `remote_script/AbletonCliRemote/`: the Remote Script that runs inside Live: contract
  (`command_backend_contract.py`), validators, handlers + registry, Live API code in
  `live_backend_parts/`. It runs standalone in Live and cannot import `ableton_cli`.
- `skills/ableton-cli/SKILL.md`: the command catalog for agents; one example line per
  command (a test enforces it).
- `docs/reference.md`: global options, wire protocol, batching, exit codes, API limits.
- `docs/skills/skill-actions.md`: stable action names (table generated from `actions.py`).
- `tests/snapshots/`: public contract and command surface snapshots.
- `tools/`: generators for the client, docs and snapshots.

## Public contract

Stable: the command surface, the JSON envelope (`ok`, `command`, `args`, `result`, `error`),
exit codes and error codes, the TCP JSONL protocol and its versioning, and the snapshots in
`tests/snapshots/`. Internal modules can be refactored freely while tests stay green.

When a command or contract changes intentionally:

1. Write the failing tests first: `test_live_backend.py`, `test_remote_command_backend.py`,
   `test_cli_new_commands.py` (or the topic files next to them).
2. Implement it on both sides (CLI command + registry row, Remote Script contract,
   validator, handler, backend part).
3. Regenerate:

       uv run python tools/generate_client_methods.py
       uv run python tools/generate_skill_docs.py
       uv run python tools/update_public_contract_snapshot.py
       uv run python tools/update_command_surface_snapshot.py

4. Update `skills/ableton-cli/SKILL.md` (example line) and README if user-facing.
5. A changed remote command set also changes `EXPECTED_COMMAND_SET_HASH` and
   `EXPECTED_REMOTE_COMMAND_COUNT` in `tests/test_command_set_hash_stability.py`; a changed
   action list changes the count in `tests/test_skill_docs.py`.

Do not regenerate snapshots to mask accidental drift.

## Shared argument shapes

When an argument shape is validated on both sides (for example MIDI note fields), keep it as
a data table of field specs, one copy per runtime (`src/ableton_cli/note_fields.py` and
`remote_script/AbletonCliRemote/note_fields.py`), and a drift test that asserts the copies
are identical (`tests/test_note_field_specs.py`).

## Remote Script rules

- Validate arguments before touching Live state; return structured errors with a hint.
- Keep handlers small; share selection, validation and Live-object access in helpers.
- Tests never assume a running Live.
- Live API calls that change state only take effect on Live's next update; do not read back
  in the same tick and assume the change is visible.

## Working rules

- Global options go before the subcommand: `ableton-cli --output json doctor`.
- Do not hard-code browser URIs, pack names or locale-dependent paths; search the browser
  and use the returned `uri` or `path`.
- Prefer stable selectors (`--track-ref`, `--device-ref`) over positions when available.
- No secrets, private absolute paths or account names in docs (a test enforces it; the
  README credit is the exception).
- The protocol listens on `127.0.0.1` only; never bind or forward it elsewhere.

## Checks

    uv run python -m ableton_cli.dev_checks

runs `ruff check`, `ruff format --check`, the Remote Script runtime check, the generated-docs
check, the contract check and `pytest`. CI runs the same plus a diff check on generated files.
Optional pre-commit hook (Ruff): `./scripts/install_git_hooks.sh`.

## Ableton operation safety

Commands mutate the user's Live Set. Before manual verification against Live, run
`ableton-cli --timeout-ms 15000 --output json doctor`; use `--read-only` for inspection and
`--plan` / `--dry-run` before destructive commands.

## Handoff

Report changed files, the public contract impact, the checks run (and any not run, with the
reason), and what still needs a manual check in Live.
