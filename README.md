# ableton-cli

Control Ableton Live 12+ from the command line: transport, tracks, clips, MIDI notes, devices,
the browser and the Arrangement. Built for scripts and AI agents: stable JSON output, fixed
exit codes, explicit errors.

> **Credits.** This is a fork of [ableton-cli](https://github.com/6uclz1/ableton-cli), created
> by **6uclz1** and contributors (MIT license). The design and nearly all of the code are
> theirs. This fork is developed independently: it adds commands for generating songs with an
> agent (see below), drops the remix/audio-analysis workflow, and does not track the original
> project.

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
| `device parameter list`, `master device parameters list`, `track info` | Parameters carry `display_value` (as Live shows it) and `value_items` for quantized parameters. |
| `device parameter set-display`, `master device parameter set-display` | Set a parameter by display value (`800 Hz`, `-6 dB`, `Saw 8`); the Remote Script finds the raw value. |
| `tracks duplicate`, `scenes duplicate\|delete`, `return-tracks create\|delete` | Song layout. |
| `arrangement locator list\|add\|add-many\|delete` | Named locators (cue points) for sections; add/delete need the transport stopped and move the playhead to the locator. |
| `transport signature set` | Time signature. |
| `arrangement back-to-arranger` | Press "Back to Arrangement"; `song info` shows `back_to_arranger`. |
| `song loop get\|set`, `song metronome set`, `song swing set`, `song groove-amount set` | Loop region, metronome, global swing and groove amount. |
| `song scale set`, `song record-quantization set`, `song capture-midi` | Key and scale (Live 12+), MIDI record quantization, Capture MIDI. |
| `scenes tempo set`, `scenes signature set` | Per-scene tempo and time signature (Live 12+), shown in `scenes list`. |
| `track monitoring get\|set`, `track fold set` | Monitoring (in/auto/off) and group folding; `tracks list` and `track info` report group state. |
| `view show`, `view select track\|scene\|clip` | Show Live's views and select tracks, scenes and clip slots. |
| `install-remote-script`, `doctor` | Find the User Library from Live's own settings. |

Not possible through the Live API: automation envelopes on Arrangement clips (put them on a
session clip and copy it), clip follow actions, saving the Set and exporting audio (the
former `song save` and `song export audio` commands always failed and were removed).

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

## Agent skill

Install the command catalog as a Claude Code skill (`~/.claude/skills/ableton-cli/SKILL.md`):

```bash
ableton-cli install-skill --yes
```

Stable action names for automation: [`docs/skills/skill-actions.md`](docs/skills/skill-actions.md).

## Development

Rules, contract changes and checks: [`AGENTS.md`](AGENTS.md).

## License

MIT, see [`LICENSE`](LICENSE).
