# ableton-cli reference

Details moved out of the README: global options, the wire protocol, batching, exit codes,
API limits and troubleshooting. The full command catalog is in
[`skills/ableton-cli/SKILL.md`](../skills/ableton-cli/SKILL.md).

## Global Options

- `--host`
- `--port`
- `--timeout-ms`
- `--protocol-version`
- `--auth-token`
- `--output [human|json]`
- `--verbose`
- `--log-file`
- `--config <path>`
- `--no-color`
- `--quiet`
- `--record <path>`
- `--replay <path>`
- `--read-only`
- `--require-confirmation`
- `--yes`
- `--plan`
- `--dry-run`
- `--compact`
- `--version`

Global options must appear before the subcommand.

```bash
# Correct
ableton-cli --output json doctor

# Incorrect
ableton-cli doctor --output json
```

Installer/config commands also support command-local forms:

- `--yes`
- `--dry-run`

## Wire protocol

`ableton-cli` uses local TCP JSONL communication on `<host>:<port>` (`127.0.0.1:8765` by
default; see [Security Model](#security-model) for overriding host/port/auth_token).

The connection can be persistent: one line is one request, and a client may
send multiple requests over the same connection. Responses are returned in
request order. A malformed request line closes the connection; well-formed
requests that fail validation or execution return a structured error and
keep the connection open.

### Event subscriptions

Commands are strictly request/response, so anything a user does in Live itself can
only be noticed by polling — that is what `session watch` does. A connection can
instead send one `"type": "subscribe"` request and become an event stream:

```json
{"type":"subscribe","name":"events","args":{"events":["tempo","is_playing"]},"meta":{},"request_id":"...","protocol_version":3}
```

The remote answers with the usual response envelope (`result.subscribed` lists the
accepted names, `result.stream` is `true`) and then pushes one line per event:

```json
{"type":"event","protocol_version":3,"event":"tempo","ts":1730000000.0,"data":{"tempo":174.0},"dropped":0}
```

- A subscribing connection stops accepting commands, so pushed events can never
  delay a command; `ableton-cli session events` opens its own connection.
- Event names are `tempo`, `is_playing`, `playing_position` and `selected_track`.
  Which of them a given Live version can deliver depends on the listener APIs it
  exposes; subscribing to one that is unavailable fails with `INVALID_ARGUMENT`
  and a hint listing what is available, rather than accepting the subscription
  and never delivering.
- `playing_position` is throttled to at most one event per 100 ms.
- A subscriber that cannot keep up loses the oldest events instead of growing an
  unbounded queue; `dropped` reports how many were lost since the previous event.
- A Remote Script that predates subscriptions rejects `"type": "subscribe"` with
  `INVALID_ARGUMENT`, so an old install fails loudly instead of hanging.

### Request envelope

```json
{
  "type": "command",
  "name": "song_info",
  "args": {},
  "meta": {
    "request_timeout_ms": 15000,
    "idempotency_key": "0f1c2d3e4f5a6b7c8d9e0f1a2b3c4d5e"
  },
  "request_id": "8c9f9b0c1a9d4dc2abdf2d53f3a19be9",
  "protocol_version": 3
}
```

`request_id` is fresh on every send and never identifies a retry.

`meta.idempotency_key` is optional (max 128 characters) and is what makes a
resend safe. The Remote Script keeps the response of the last 256 completed
keys; a request repeating a key it has already completed is **not executed
again** — the stored response is returned with `idempotent_replay: true` added
to `result` (or to `error.details` for a stored failure). `batch run` and
`batch stream` generate one key per step and reuse it for every retry attempt,
so a step that times out and is retried cannot be applied twice.

Protocol versions must match exactly. After upgrading the CLI, reinstall the
Remote Script and re-select the Control Surface in Live:

```bash
ableton-cli install-remote-script --yes
```

### Response (success)

```json
{
  "ok": true,
  "request_id": "8c9f9b0c1a9d4dc2abdf2d53f3a19be9",
  "protocol_version": 3,
  "result": {
    "tempo": 120.0
  },
  "error": null
}
```

### Response (failure)

```json
{
  "ok": false,
  "request_id": "8c9f9b0c1a9d4dc2abdf2d53f3a19be9",
  "protocol_version": 3,
  "result": null,
  "error": {
    "code": "INVALID_ARGUMENT",
    "message": "bpm must be between 20.0 and 999.0",
    "hint": "Fix command arguments and retry.",
    "details": null
  }
}
```

## Batching and low latency

For single commands, use existing subcommands as before.
For repeated automation commands, prefer `batch stream` to keep one process alive and avoid process startup overhead.

`batch stream` expects one JSON object per stdin line and emits one JSON response line per request:

```bash
cat <<'JSONL' | ableton-cli batch stream
{"id":"a1","steps":[{"name":"song_info","args":{}}]}
{"id":"a2","steps":[{"name":"track_volume_get","args":{"track_ref":{"mode":"index","index":0}}}]}
JSONL
```

Compatibility validation is now explicit:

- `ableton-cli ping` for protocol/version metadata
- `ableton-cli doctor` for supported command integrity checks

### Batch step retries

Batch steps run once unless the step opts in with a `retry` object:

```json
{"name": "tracks_list", "args": {}, "retry": {"max_attempts": 3, "backoff_ms": 200}}
```

`retry.on` defaults to `["REMOTE_BUSY"]`. `REMOTE_BUSY` is rejected by the
Remote Script before the command is queued, so a retry cannot double-apply it.

`TIMEOUT` is not retried by default, but adding it to `retry.on` is safe for
any command: a retrying step carries one `meta.idempotency_key` across all of
its attempts, so the Remote Script replays its stored response rather than
applying the command a second time. A replayed response carries
`idempotent_replay: true`.

A step that fails with `TIMEOUT` and is not retried reports
`error.details.may_have_executed`:

- `true` — Live had already started the command; inspect the set before retrying
- `false` — the command was cancelled before it ran and can be resent safely
- `null` — no structured answer reached the CLI; assume it may have been applied

## Exit Codes

- `0` success
- `2` invalid arguments
- `3` invalid configuration
- `10` Ableton not connected
- `11` Remote Script not installed/detected
- `12` timeout
- `13` protocol mismatch
- `20` execution failure
- `99` internal error

## Unsupported-by-API behavior

If a command is exposed by CLI/Remote but Live API cannot perform it, the command fails explicitly with:

- `error.code=INVALID_ARGUMENT`
- `error.details.reason=not_supported_by_live_api`

This currently applies to API-limited operations such as `song new/undo/redo/save/export`, `arrangement record start|stop`, `scenes move`, and `tracks delete` when the running Live API lacks the required primitive.

Clip and arrangement note write/edit commands (`clip notes add`, `clip notes update`,
`clip notes quantize|humanize|velocity-scale|transpose`, `arrangement clip notes add`, and
`clip cut-to-drum-rack` trigger clip creation) require the Live 12+ extended note API
(`Clip.add_new_notes` / `Clip.apply_note_modifications`, plus the `note_id`, `probability`,
`velocity_deviation`, and `release_velocity` note fields). On older Live versions these commands
fail with the `not_supported_by_live_api` reason above instead of falling back to the legacy
note API.

## Not-implemented commands

Some commands are part of the published surface but have no working implementation behind
them, because the Live API does not expose the primitive (creating return or group tracks,
sidechain routing) or because the work happens outside this CLI (stem separation, browser
target discovery). They fail explicitly rather than returning a plan nobody executes:

- `error.code=NOT_IMPLEMENTED`
- `error.details.reason=not_implemented`
- exit code `20`
- `error.hint` names the commands that do the job

This currently applies to `remix setup-sound`, `remix mix-macro`, `remix setup-mix`,
`remix setup-returns`, `remix setup-sidechain`, `remix device-chain apply`, and
`audio stems split`. Argument validation still runs first, so a bad argument reports
`INVALID_ARGUMENT` and exit code `2`.

## Completion

Typer built-in completion is available:

```bash
ableton-cli --install-completion
ableton-cli --show-completion
```

## Man Page

Generate:

```bash
scripts/generate_man.sh
```

Install locally (optional):

```bash
scripts/install_man.sh
```

Then:

```bash
man ableton-cli
```

## Troubleshooting

1. Run `ableton-cli doctor`.
2. Confirm Ableton is running and `AbletonCliRemote` is selected as Control Surface.
3. Confirm host/port (`127.0.0.1:8765` by default).
4. Try a longer timeout: `--timeout-ms 30000`.
5. If protocol mismatches, the installed Remote Script is from a different release:
   run `ableton-cli install-remote-script --yes`, restart Ableton Live, and re-select
   `AbletonCliRemote` as Control Surface. Use `--protocol-version <n>` or
   `ableton-cli config set protocol_version <n>` only to talk to a deliberately pinned
   Remote Script version.

### `AbletonCliRemote` not shown in Control Surface list

1. Reinstall the script files: `ableton-cli install-remote-script --yes`.
2. Restart Ableton Live completely.
3. Run `ableton-cli --output json doctor` and check:
   - `remote_script_files`
   - `remote_script_entrypoint`
4. Verify installed paths. `install-remote-script` and `doctor` use the User Library set in
   Live's preferences (`Library.cfg`, newest Live version first), then the defaults:
   - `~/Music/Ableton/User Library/Remote Scripts/AbletonCliRemote` (macOS)
   - `~/Documents/Ableton/User Library/Remote Scripts/AbletonCliRemote`

### Remote Script update not taking effect immediately

If behavior still looks old after `install-remote-script --yes` (for example, unchanged command errors):

1. In Ableton Live Preferences, set Control Surface to `None`.
2. Set it back to `AbletonCliRemote`.
3. Re-run `ableton-cli --output json ping` and `ableton-cli --output json doctor`.
4. If unchanged, restart Ableton Live and retry.
