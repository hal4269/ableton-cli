# ableton-cli

Control Ableton Live 12+ from the command line: transport, tracks, clips, MIDI notes, devices,
the browser and the Arrangement. Built for scripts and AI agents: stable JSON output, fixed
exit codes, explicit errors.

> **Credits.** This is a fork of [ableton-cli](https://github.com/6uclz1/ableton-cli), created
> by **6uclz1** and contributors (MIT license). The design and nearly all of the code are
> theirs. This fork adds a few commands for generating songs with an agent (see below) and
> keeps its changes small so they can go back upstream.

## How it works

```
ableton-cli  --JSON lines over TCP 127.0.0.1:8765-->  AbletonCliRemote (Remote Script in Live)  -->  Live API
```

The CLI and the Remote Script must come from the same commit.

## Install

Requirements: Ableton Live 12+, Python 3.10+, [uv](https://docs.astral.sh/uv/).

```bash
git clone <repo-url> ableton-cli
uv tool install --force --editable ./ableton-cli   # puts `ableton-cli` on PATH
ableton-cli install-remote-script --yes
```

`install-remote-script` looks in `~/Documents` and `~/Music`. If your Documents folder is
redirected, copy `remote_script/AbletonCliRemote` into `User Library/Remote Scripts/` yourself.

In Live: **Preferences → Link, Tempo & MIDI → Control Surface → `AbletonCliRemote`**. Then:

```bash
ableton-cli doctor   # remote_ping must PASS
ableton-cli ping     # protocol version and supported commands
```

After every Remote Script update, **restart Live**. Re-selecting the control surface does not
reload the code.

## Usage

Global options go **before** the subcommand: `ableton-cli --output json tracks list`.

```bash
ableton-cli transport tempo set 128
ableton-cli tracks create midi --index 0
ableton-cli browser search "Operator" --item-type loadable --limit 5
ableton-cli browser load 0 "<path-or-uri-from-search>"
ableton-cli clip create 0 0 --length 16
ableton-cli clip notes add 0 0 --notes-json '[{"pitch":60,"start_time":0.0,"duration":0.5,"velocity":100,"mute":false}]'
ableton-cli arrangement clip from-session 0 0 --start 0
ableton-cli device parameter set --track-index 0 --device-index 0 --parameter-index 1 -- 0.5
```

Browser contents differ per Live version, packs and locale, so search first and load the
returned `path` or `uri`:

```bash
ableton-cli browser search "Drum Rack" --path drums --item-type loadable --limit 10
ableton-cli browser search "Kit" --path drums --item-type loadable --limit 10
```

With `--output json` every command prints one envelope:

```json
{"ok": true, "command": "ping", "args": {}, "result": {}, "error": null}
```

Many calls in a row? Use `batch run --steps-file steps.json` or `batch stream` (one process,
JSON lines on stdin).

- All commands: [`skills/ableton-cli/SKILL.md`](skills/ableton-cli/SKILL.md)
- Global options, exit codes, batching, API limits, troubleshooting:
  [`docs/reference.md`](docs/reference.md)

## What this fork adds

| Command | Change |
| --- | --- |
| `clip duplicate`, `clip duplicate-many` | Exact copy (`ClipSlot.duplicate_clip_to`): keeps clip envelopes, note probability and loop settings. |
| `arrangement clip from-session <track> <slot> --start <beats>` | New. Exact copy of a session clip into the Arrangement, without real-time recording. |
| `clip delete <track> <slot>` | New. Deletes a session clip. |
| `device chains list` | Reports `in_note` per chain: the MIDI note of each Drum Rack pad. |

Not possible through the Live API: automation envelopes on Arrangement clips. Put the envelope
on a session clip and copy that clip instead.

## Protocol

One JSON object per line over local TCP; request/response; a connection may stay open. Every
request carries a `protocol_version` that must match the Remote Script exactly, and retries
reuse an idempotency key so a write is never applied twice. A connection can instead subscribe
to events (`tempo`, `is_playing`, `playing_position`, `selected_track`). Envelopes and details:
[`docs/reference.md`](docs/reference.md#wire-protocol).

## Security Model

- The Remote Script listens on 127.0.0.1 only, port 8765, with no authentication by default:
  any local process can control Live. Never expose or forward this port.
- Host, port and an optional shared `auth_token` can be set in
  `remote_script/AbletonCliRemote/remote_config.json` or with `ABLETON_CLI_REMOTE_HOST`,
  `ABLETON_CLI_REMOTE_PORT`, `ABLETON_CLI_REMOTE_AUTH_TOKEN`. On the CLI side use
  `--auth-token`, `ABLETON_CLI_AUTH_TOKEN` or `ableton-cli config set auth_token <token>`.
  The token is a deterrent, not encryption.
- Commands act like a user in Live. Use `--read-only` for inspection, `--plan` or `--dry-run`
  to preview a change, and `--require-confirmation --yes` to make destructive commands fail
  unless confirmed.

## Skills Integration

Install the agent skill (the command catalog) for Codex, Claude Code or Cursor:

```bash
uv run ableton-cli install-skill --yes                   # Codex (needs CODEX_HOME)
uv run ableton-cli install-skill --target claude --yes
uv run ableton-cli install-skill --target cursor --yes
```

Details: [`docs/skills/install.md`](docs/skills/install.md). Stable action names:
[`docs/skills/skill-actions.md`](docs/skills/skill-actions.md).

## Contributing

Development workflow, tests and quality gates: [`CONTRIBUTING.md`](CONTRIBUTING.md).

## License

MIT, see [`LICENSE`](LICENSE).
