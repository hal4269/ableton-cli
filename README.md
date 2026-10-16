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

`install-remote-script` installs into the User Library set in Live's preferences (also when it
is moved or your Documents folder is redirected), else `~/Documents` or `~/Music`.

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
| `clip duplicate`, `clip duplicate-many` | Exact copy: keeps clip envelopes, note probability and loop settings. |
| `arrangement clip from-session`, `arrangement from-session` | Exact copies of session clips in the Arrangement (envelopes, probability), without recording. |
| `clip delete` | Delete a session clip. |
| `clip color set`, `track color set` | Clip and track colors (0-69). |
| `clip launch get\|set` | Launch mode, quantization, legato, velocity amount. |
| `clip envelope mixer set\|shape\|clear <track> <clip> volume\|panning\|send [--send-index N]` | Clip envelopes for the track mixer (volume, panning, sends), not only device parameters. |
| `clip crop`, `clip duplicate-loop`, `clip signature set` | Crop to the loop, double the loop (MIDI), clip time signature (also in `clip props get`). |
| `device delete`, `device move`, `device enabled set`, `device parameter list` | Edit any track's device chain; also devices inside racks via `--device-ref`. |
| `device chains list` | Reports `in_note` per chain: the MIDI note of each Drum Rack pad. |
| `device chains get\|set` | Rack chain volume, panning, mute, solo and Drum Rack choke group (also listed by `device chains list`). |
| `device variation list\|store\|recall\|delete` | Rack macro variations. |
| `device insert` | Insert a native device by name at a position (Live 12.1.10+). |
| `device parameter list`, `track info` | Parameters carry `display_value` (as Live shows it) and `value_items` for quantized parameters. |
| `tracks duplicate`, `scenes duplicate\|delete`, `return-tracks create\|delete` | Song layout. |
| `arrangement locator list\|add\|delete` | Named locators (cue points) for sections. |
| `transport signature set` | Time signature. |
| `install-remote-script`, `doctor` | Find the User Library from Live's own settings. |

Not possible through the Live API: automation envelopes on Arrangement clips (put them on a
session clip and copy it) and clip follow actions.

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
