---
name: ableton-cli
description: Control and inspect Ableton Live with ableton-cli in non-interactive workflows. Use when an agent or script needs deterministic setup checks, transport control, track and clip operations, browser loading, and stable JSON command mappings.
---

# Ableton Live Control with ableton-cli

## Quick start

```bash
ableton-cli doctor
ableton-cli ping
ableton-cli song info
ableton-cli transport play
ableton-cli transport stop
```

## Commands

### Setup / Diagnostics

```bash
ableton-cli doctor
ableton-cli install-remote-script --yes
ableton-cli install-remote-script --dry-run
ableton-cli install-skill --yes
ableton-cli install-skill --dry-run
ableton-cli ping
ableton-cli wait-ready
```

After `install-remote-script --yes`, if behavior does not change immediately, reload the control surface in Ableton Preferences (`None` -> `AbletonCliRemote`) or restart Ableton Live.

To verify that the latest Remote Script is active, run `ableton-cli --output json ping` and confirm:
- `result.remote_script_version` is the expected version
- `result.supported_commands` includes the newly added command names

### Song / Session

```bash
ableton-cli song info
ableton-cli song new
ableton-cli song undo
ableton-cli song redo
ableton-cli song loop get
ableton-cli song loop set --enabled --start 64 --length 32
ableton-cli song metronome set false
ableton-cli song swing set 0.25
ableton-cli song groove-amount set 1.0
ableton-cli song scale set --root A --name Minor --mode
ableton-cli song record-quantization set 1/16
ableton-cli song capture-midi --destination session
ableton-cli session info
ableton-cli session events --events tempo,is_playing --count 5
ableton-cli session events --idle-timeout-ms 5000
ableton-cli session stop-all-clips
```

`song info` also reports `back_to_arranger`, the loop region, metronome, swing and groove
amounts, the key/scale (`scale.root_note` 0-11, `scale.name`, `scale.mode`), MIDI record
quantization and `can_capture_midi`. Saving the Set and exporting audio are not in Live's
API: do them in Live (Ctrl/Cmd+S, File > Export Audio/Video).

### View

```bash
ableton-cli view show arranger
ableton-cli view show device-chain
ableton-cli view select track 2
ableton-cli view select scene 1
ableton-cli view select clip 2 0
```

`view show` takes `session`, `arranger`, `detail`, `clip` (Detail/Clip) or `device-chain`
(Detail/DeviceChain).

### Tracks

```bash
ableton-cli tracks list
ableton-cli tracks create midi
ableton-cli tracks create midi --index 1
ableton-cli tracks create audio
ableton-cli tracks create audio --index 1
ableton-cli tracks delete 2
ableton-cli tracks duplicate 1
```

### Transport

```bash
ableton-cli transport play
ableton-cli transport stop
ableton-cli transport toggle
ableton-cli transport tempo get
ableton-cli transport tempo set 128
ableton-cli transport position get
ableton-cli transport position set 32
ableton-cli transport rewind
ableton-cli transport signature set 7 8
```

### Arrangement

```bash
ableton-cli arrangement record start
ableton-cli arrangement record stop
ableton-cli arrangement clip create 0 --start 8 --length 4
ableton-cli arrangement clip create 0 --start 8 --length 4 --notes-json '[{"pitch":60,"start_time":0.0,"duration":0.5,"velocity":100,"mute":false}]'
ableton-cli arrangement clip create 1 --start 16 --length 8 --audio-path /tmp/loop.wav
ableton-cli arrangement clip list
ableton-cli arrangement clip list --track 0
ableton-cli arrangement clip notes add 0 0 --notes-file ./notes.json
ableton-cli arrangement clip notes get 0 0 --start-time 0.0 --end-time 4.0 --pitch 60
ableton-cli arrangement clip notes clear 0 0 --pitch 60
ableton-cli arrangement clip notes replace 0 0 --notes-json '[{"pitch":65,"start_time":0.25,"duration":0.5,"velocity":100,"mute":false}]'
ableton-cli arrangement clip notes import-browser 0 0 sounds/Bass\ Loop.alc --mode replace --import-length --import-groove
ableton-cli arrangement clip delete 0 0
ableton-cli arrangement clip delete 0 --start 8 --end 16
ableton-cli arrangement clip delete 0 --all
ableton-cli arrangement clip props get 0 0
ableton-cli arrangement clip loop set 0 0 --start 0 --end 16 --enabled true
ableton-cli arrangement clip marker set 0 0 --start-marker 0 --end-marker 16
ableton-cli arrangement clip warp get 0 0
ableton-cli arrangement clip warp set 0 0 --enabled true --mode beats
ableton-cli arrangement clip gain set 0 0 --db -6
ableton-cli arrangement clip transpose set 0 0 --semitones -1
ableton-cli arrangement clip file replace 0 0 --audio-path /tmp/replacement.wav
ableton-cli arrangement clip from-session 0 2 --start 64
ableton-cli arrangement from-session --scenes "0:24,1:48"
ableton-cli arrangement locator list
ableton-cli arrangement locator add 64 --name "Drop"
ableton-cli arrangement locator add-many --locators-json '[{"time":0,"name":"Intro"},{"time":64,"name":"Drop"}]' --skip-existing
ableton-cli arrangement locator delete 0
ableton-cli arrangement back-to-arranger
```

Launching Session clips takes tracks off the Arrangement (Live lights the "Back to
Arrangement" button; `song info` shows `back_to_arranger: true`). `arrangement
back-to-arranger` presses it, so every track plays the Arrangement again.

`arrangement clip from-session` and `arrangement from-session` place exact copies of session
clips (clip envelopes, note probability, loop settings). `arrangement from-session` tiles a
clip over the scene duration; a copy that runs past the end keeps its full length, so use
durations that are a multiple of the clip lengths.

Locators: Live only toggles a cue point at the playhead, and applies a playhead move on its
next update. So `locator add|delete` need the transport stopped, move the playhead to the
locator (`transport position set`), wait until `transport position get` reports it, then
toggle; the playhead stays there. `locator add-many` adds a list that way in one call and
then returns the playhead to where it was. Live refuses positions behind the song length.

### Track

```bash
ableton-cli track info --track-index 0
ableton-cli track volume get --track-index 0
ableton-cli track volume set 0.7 --track-index 0
ableton-cli track name set "Lead Synth" --track-index 0
ableton-cli track mute get --track-index 0
ableton-cli track mute set true --track-index 0
ableton-cli track solo get --track-index 0
ableton-cli track solo set true --track-index 0
ableton-cli track arm get --track-index 0
ableton-cli track arm set false --track-index 0
ableton-cli track panning get --track-index 0
ableton-cli track panning set -- -0.25 --track-index 0
ableton-cli track send get 1 --track-index 0
ableton-cli track send set 1 0.6 --track-index 0
ableton-cli track routing input get --selected-track
ableton-cli track routing input set --type Ext.\ In --channel 1/2 --track-index 0
ableton-cli track routing output get --track-index 0
ableton-cli track routing output set --type Master --channel 3/4 --track-index 0
ableton-cli track color set 12 --track-name "Bass"
ableton-cli track monitoring get --track-index 0
ableton-cli track monitoring set in --track-index 0
ableton-cli track fold set true --track-name "Drums"
```

`tracks list` and `track info` report group state: `is_foldable` (group track),
`fold_state` (null unless foldable), `is_grouped` and `group_track` (index of the
containing group). Group tracks have no monitoring state; `track monitoring` fails on them.

Ref-aware commands use selector flags, not positional indexes.
Track selectors: `--track-index`, `--track-name`, `--selected-track`, `--track-query`, `--track-ref`.
Device selectors: `--device-index`, `--device-name`, `--selected-device`, `--device-query`, `--device-ref`.
Parameter selectors: `--parameter-index`, `--parameter-name`, `--parameter-query`, `--parameter-key`, `--parameter-ref`.
Reuse `stable_ref` values emitted by `tracks list`, `track info`, synth/effect finds, and parameter listings when you need an exact session-local target.

### Return Track

```bash
ableton-cli return-tracks list
ableton-cli return-tracks create
ableton-cli return-tracks delete 1
ableton-cli return-track volume get 0
ableton-cli return-track volume set 0 0.5
ableton-cli return-track mute get 0
ableton-cli return-track mute set 0 true
ableton-cli return-track solo get 0
ableton-cli return-track solo set 0 false
```

### Master / Mixer

```bash
ableton-cli master info
ableton-cli master volume get
ableton-cli master volume set 0.85
ableton-cli master panning get
ableton-cli master panning set -- 0.0
ableton-cli master devices list
ableton-cli master device load query:Audio\ Effects#Utility --position end
ableton-cli master device move --device-index 2 --to-index 0
ableton-cli master device delete --device-index 3 --yes
ableton-cli master device parameters list --device-index 0
ableton-cli master device parameter set --device-index 0 --parameter-key gain -- -1.5
ableton-cli master device parameter set-display --device-index 0 --parameter-name Gain -- "-1.5 dB"
ableton-cli master effect eq8 keys
ableton-cli master effect eq8 set 0.42 --device-query "EQ Eight" --parameter-key band1_gain
ableton-cli master effect eq8 observe --device-query "EQ Eight"
ableton-cli master effect limiter keys
ableton-cli master effect limiter set 0.4 --device-query "Limiter" --parameter-key ceiling
ableton-cli master effect limiter observe --device-query "Limiter"
ableton-cli master effect compressor keys
ableton-cli master effect compressor set 0.3 --device-query "Compressor" --parameter-key ratio
ableton-cli master effect compressor observe --device-query "Compressor"
ableton-cli master effect utility keys
ableton-cli master effect utility set 0.5 --device-query "Utility" --parameter-key gain
ableton-cli master effect utility observe --device-query "Utility"
ableton-cli mixer crossfader get
ableton-cli mixer crossfader set -- -0.2
ableton-cli mixer cue-volume get
ableton-cli mixer cue-volume set 0.75
ableton-cli mixer cue-routing get
ableton-cli mixer cue-routing set Ext.\ Out
```

### Clip

```bash
ableton-cli clip create 0 0 --length 4
ableton-cli clip notes add 0 0 --notes-json '[{"pitch":60,"start_time":0.0,"duration":0.5,"velocity":100,"mute":false}]'
ableton-cli clip notes add 0 0 --notes-file ./notes.json
ableton-cli clip notes add 0 0 --pattern "c3 ~ [e3 g3] c4*2" --pattern-length 4
ableton-cli clip notes get 0 0 --start-time 0.0 --end-time 4.0 --pitch 60
ableton-cli clip notes clear 0 0 --start-time 0.0 --end-time 1.0
ableton-cli clip notes replace 0 0 --notes-json '[{"pitch":65,"start_time":0.25,"duration":0.5,"velocity":100,"mute":false}]' --start-time 0.0 --end-time 1.0
ableton-cli clip notes update 0 0 --notes-json '[{"note_id":3,"velocity":90,"probability":0.75}]'
ableton-cli clip notes import-browser 0 1 sounds/Bass\ Loop.alc --mode replace --import-length --import-groove
ableton-cli clip notes quantize 0 0 --grid 1/16 --strength 0.8 --start-time 0.0 --end-time 4.0
ableton-cli clip notes humanize 0 0 --timing 0.05 --velocity 5
ableton-cli clip notes velocity-scale 0 0 --scale 1.1 --offset -3
ableton-cli clip notes transpose 0 0 --semitones 2 --start-time 0.0 --end-time 4.0
ableton-cli clip notes transpose-in-scale 0 0 --root C --scale major --degrees 1
ableton-cli clip notes arpeggiate 0 0 --mode up --rate 1/16 --gate 0.9
ableton-cli clip notes arpeggiate 0 0 --mode random --seed 42
ableton-cli clip notes euclidean 0 0 --pitch 36 --steps 16 --pulses 5 --length 4 --mode replace
ableton-cli clip notes ratchet 0 0 --division 2 --probability 1.0
ableton-cli clip notes ratchet 0 0 --division 4 --probability 0.6 --seed 42
ableton-cli clip notes retrograde 0 0 --loop-length 4
ableton-cli clip envelope set 0 0 --points-json '[{"time":0.0,"value":0.1},{"time":4.0,"value":0.9}]' --device-index 0 --parameter-key filter_cutoff
ableton-cli clip envelope shape 0 0 --device-index 0 --parameter-key filter_cutoff --shape ramp --from 0.1 --to 0.9 --start 0 --length 4 --resolution 16
ableton-cli clip envelope clear 0 0 --device-index 0 --parameter-key filter_cutoff
ableton-cli clip envelope clear 0 0 --all
ableton-cli clip envelope mixer set 0 0 volume --points-json '[{"time":0.0,"value":0.0},{"time":4.0,"value":0.85}]'
ableton-cli clip envelope mixer shape 0 0 send --send-index 0 --shape lfo-sine --from 0 --to 0.6 --length 16 --rate 0.25
ableton-cli clip envelope mixer clear 0 0 panning
ableton-cli clip groove get 0 0
ableton-cli clip groove set 0 0 grooves/Hip\ Hop\ Boom\ Bap\ 16ths\ 90\ bpm.agr
ableton-cli clip groove amount set 0 0 0.6
ableton-cli clip groove clear 0 0
ableton-cli clip name set 0 0 "Hook"
ableton-cli clip name set-many 0 --map "1:Main,2:Var,5:Peak"
ableton-cli clip fire 0 0
ableton-cli clip stop 0 0
ableton-cli clip delete 0 3
ableton-cli clip color set 0 0 12
ableton-cli clip launch get 0 0
ableton-cli clip launch set 0 0 --mode trigger --quantization 1 --legato --velocity-amount 0.5
ableton-cli clip crop 0 0
ableton-cli clip duplicate-loop 0 0
ableton-cli clip signature set 0 0 7 8
ableton-cli clip active get 0 0
ableton-cli clip active set 0 0 false
ableton-cli clip duplicate 0 0 1
ableton-cli clip duplicate-many 0 0 --to 2,4,5,6
ableton-cli clip place-pattern 0 --clip 0 --scenes Intro,Drop,Peak
ableton-cli clip props get 0 0
ableton-cli clip loop set 0 0 --start 0 --end 16 --enabled true
ableton-cli clip marker set 0 0 --start-marker 0 --end-marker 16
ableton-cli clip warp get 0 0
ableton-cli clip warp set 0 0 --enabled true --mode complex-pro
ableton-cli clip warp-marker list 0 0
ableton-cli clip warp-marker add 0 0 --beat-time 33.0
ableton-cli clip warp-marker add 0 0 --beat-time 33.0 --sample-time 12.345
ableton-cli clip warp-marker move 0 0 --beat-time 33.0 --distance -0.5
ableton-cli clip warp-marker remove 0 0 --beat-time 33.0
ableton-cli clip gain set 0 0 --db -3.0
ableton-cli clip transpose set 0 0 --semitones 2
ableton-cli clip file replace 0 0 --audio-path /tmp/replacement.wav
ableton-cli clip file path get 0 0
```

`clip envelope set|shape|clear` target a device parameter (device + parameter selectors);
`clip envelope mixer set|shape|clear` target the track's own mixer: `volume` (0.0-1.0,
0.85 = 0 dB), `panning` (-1.0 to 1.0) or `send` with `--send-index` (0 = send A, 0.0-1.0).
Values are checked against the parameter's range.
`clip crop`, `clip duplicate-loop` and `clip signature set` return the clip properties.

### Scenes

```bash
ableton-cli scenes list
ableton-cli scenes create
ableton-cli scenes create --index 1
ableton-cli scenes name set 1 "Build"
ableton-cli scenes fire 1
ableton-cli scenes move 1 2
ableton-cli scenes duplicate 1
ableton-cli scenes delete 2
ableton-cli scenes tempo set 1 128
ableton-cli scenes tempo set 1 --clear
ableton-cli scenes signature set 1 7 8
ableton-cli scenes signature set 1 --clear
```

`scenes list` shows each scene's `tempo` and `signature` (null when the scene does not set
them). Live 12+.

### Browser

```bash
ableton-cli browser tree all
ableton-cli browser items-at-path drums/Kits
ableton-cli browser item drums/Kits
ableton-cli browser item query:Synths#Operator
ableton-cli browser categories all
ableton-cli browser items drums/Kits --item-type loadable --limit 100 --offset 0
ableton-cli browser search drift --item-type loadable
ableton-cli browser search "Drum Rack" --path drums --item-type loadable --limit 10
ableton-cli browser search "Kit" --path drums --item-type loadable --limit 10
ableton-cli browser load 0 query:Synths#Operator
ableton-cli browser load 0 instruments/Drift
ableton-cli browser load-drum-kit 0 <rack-uri-from-search> --kit-uri <kit-uri-from-search>
ableton-cli browser load-drum-kit 0 <rack-uri-from-search> --kit-path <kit-path-from-search>
```

For composition workflows, do not hard-code Drum Rack or kit targets. First run
`ableton-cli --timeout-ms 15000 --output json wait-ready`, then use `browser search`
to select exact `uri` or `path` values from the active Live browser catalog before calling
`browser load-drum-kit` or `browser load`.

### Batch

```bash
ableton-cli batch run --steps-file ./steps.json
ableton-cli batch run --steps-json '{"steps":[{"name":"song_info","args":{}}]}'
echo '{"steps":[{"name":"song_info","args":{}}]}' | ableton-cli batch run --steps-stdin
ableton-cli batch stream
echo '{"id":"req-1","steps":[{"name":"song_info","args":{}}]}' | ableton-cli batch stream
```

### Device

```bash
ableton-cli device parameter set 0.25 --track-index 0 --device-index 0 --parameter-index 0
ableton-cli device parameter set-display "800 Hz" --track-index 0 --device-index 0 --parameter-name "Filter Freq"
ableton-cli device chains list --track-index 0 --device-index 0
ableton-cli device macro list --track-index 0 --device-index 0
ableton-cli device macro set 0 64.0 --track-index 0 --device-index 0
ableton-cli device parameter set 0.5 --track-index 0 --device-ref device:12 --parameter-index 0
ableton-cli device parameter list --track-index 0 --device-ref device:12
ableton-cli device delete --track-index 0 --device-index 2
ableton-cli device move --to-index 0 --track-index 0 --device-index 2
ableton-cli device enabled set false --track-index 0 --device-index 1
ableton-cli device insert "EQ Eight" --track-index 0 --index 1
ableton-cli device chains get 2 --track-index 0 --device-index 0
ableton-cli device chains set 2 --volume 0.7 --panning -0.2 --mute --track-index 0 --device-index 0
ableton-cli device chains set 5 --choke-group 1 --no-solo --track-index 0 --device-index 0
ableton-cli device variation list --track-index 0 --device-index 0
ableton-cli device variation store --track-index 0 --device-index 0
ableton-cli device variation recall 1 --track-index 0 --device-index 0
ableton-cli device variation delete 1 --track-index 0 --device-index 0
```

Devices inside rack chains: take the `stable_ref` from `device chains list` and pass it as
`--device-ref` to `device parameter list|set`, `device delete` or `device enabled set`.
`device move` moves top-level devices only.

`device chains list` reports `in_note` per chain: the MIDI note that triggers a Drum Rack pad
(`null` for other racks). Use it to map pads; chain order is not the note order.

`device chains list|get` also report each chain's `volume`, `panning` (with Live's display
strings `volume_display`, `panning_display`), `mute`, `solo` and `choke_group` (Drum Rack
chains: 0 = none, 1-16; `null` for other racks). `device chains set` changes only the given
options; `--choke-group` needs a Drum Rack. Racks nested in a chain: pass their `stable_ref`
as `--device-ref`.

Parameter listings (`device parameter list`, `master device parameters list`,
`synth|effect parameters list`, `track info`) include `display_value`, the value as Live shows
it (e.g. `-6.0 dB`, `Soft Sine`), and, for quantized parameters, `value_items` (the option
names; the value is the item's index). `device parameter set-display` and
`master device parameter set-display` take such a value (`800 Hz`, `1.2 kHz`, `120 ms`,
`-6 dB`, `-inf dB`, `35 %`, or an item name): the Remote Script finds the raw value by
bisection on Live's own display, in one call. Values out of range fail with the range.

`device insert` adds a native Live device by name at a position on a track (Live 12.1.10+,
`Track.insert_device`); without `--index` it appends. Use `browser load` for presets and
plug-ins.

`device variation recall|delete <index>` select that macro variation first (Live works on the
selected variation).

### Synth

```bash
ableton-cli synth find
ableton-cli synth find --track 0 --type wavetable
ableton-cli synth parameters list --track-index 0 --device-index 0
ableton-cli synth parameter set 0.5 --track-index 0 --device-index 0 --parameter-index 0
ableton-cli synth observe --track-index 0 --device-index 0
ableton-cli synth wavetable keys
ableton-cli synth wavetable set 0.6 --track-index 0 --device-index 0 --parameter-key filter_cutoff
ableton-cli synth wavetable observe --track-index 0 --device-index 0
ableton-cli synth drift keys
ableton-cli synth drift set 0.4 --track-index 0 --device-index 0 --parameter-key drift_amount
ableton-cli synth drift observe --track-index 0 --device-index 0
ableton-cli synth meld keys
ableton-cli synth meld set 0.3 --track-index 0 --device-index 0 --parameter-key spread_amount
ableton-cli synth meld observe --track-index 0 --device-index 0
```

### Effect

```bash
ableton-cli effect find
ableton-cli effect find --track 0 --type eq8
ableton-cli effect parameters list --track-index 0 --device-index 0
ableton-cli effect parameter set 0.5 --track-index 0 --device-index 0 --parameter-index 0
ableton-cli effect parameter set -- -2.0 --track-index 0 --device-index 0 --parameter-index 7
ableton-cli effect observe --track-index 0 --device-index 0
ableton-cli effect eq8 keys
ableton-cli effect eq8 set 0.6 --track-index 0 --device-index 0 --parameter-key band1_freq
ableton-cli effect eq8 observe --track-index 0 --device-index 0
ableton-cli effect limiter keys
ableton-cli effect limiter set 0.4 --track-index 0 --device-index 0 --parameter-key ceiling
ableton-cli effect limiter observe --track-index 0 --device-index 0
ableton-cli effect compressor keys
ableton-cli effect compressor set 0 0 ratio 0.5
ableton-cli effect compressor observe 0 0
ableton-cli effect auto-filter keys
ableton-cli effect auto-filter set 0 0 lfo_rate 0.25
ableton-cli effect auto-filter observe 0 0
ableton-cli effect reverb keys
ableton-cli effect reverb set 0 0 size 0.55
ableton-cli effect reverb observe 0 0
ableton-cli effect utility keys
ableton-cli effect utility set 0 0 width 0.75
ableton-cli effect utility observe 0 0
```

### Config / Completion

```bash
ableton-cli config init
ableton-cli config init --dry-run
ableton-cli config show
ableton-cli config set protocol_version 3
ableton-cli completion
ableton-cli --install-completion
ableton-cli --show-completion
```

## Operational notes

- For positional numeric arguments that begin with `-`, insert `--` before the value.
  - Example: `ableton-cli track panning set -- -0.25 --track-index 0`
  - Example: `ableton-cli effect parameter set -- -2.0 --track-index 0 --device-index 0 --parameter-index 7`
- For low-latency repeated automation operations, prefer `ableton-cli batch stream`.
- Capability and compatibility checks are explicit through `ableton-cli ping` and `ableton-cli doctor`.
- Batch steps run once unless the step declares `retry`. `retry.on` defaults to `["REMOTE_BUSY"]`.
  - A retrying step carries one `meta.idempotency_key` across every attempt, so the Remote Script replays its stored response instead of applying the command twice. Adding `TIMEOUT` to `retry.on` is therefore safe for write commands too.
  - A replayed response is marked with `idempotent_replay: true` in `result` (or in `error.details` for a replayed failure).
  - A `TIMEOUT` step failure that is not retried reports `error.details.may_have_executed` (`true` / `false` / `null` when unknown). Inspect the set with a read command before resending anything other than `false`.
- Protocol version 3 is required. On `PROTOCOL_VERSION_MISMATCH`, run `ableton-cli install-remote-script --yes`, restart Ableton Live, and re-select `AbletonCliRemote`.
- Destructive master device deletion requires `--yes`. Live API unsupported operations fail explicitly with `not_supported_by_live_api`.
- Standard wrapper commands (`synth <type> ...`, `effect <type> ...`) are strict and intentionally fail if required parameter names are missing.
  - If you get `Missing required standard ... keys`, use generic commands instead:
    - `ableton-cli --output json effect parameters list --track-index <track> --device-index <device>`
    - `ableton-cli --output json effect parameter set <value> --track-index <track> --device-index <device> --parameter-index <parameter>`
  - Use this path for locale/device-variant differences to avoid workflow stalls.

## Global options

- `--host`
- `--port`
- `--timeout-ms`
- `--protocol-version`
- `--output [human|json]`
- `--verbose`
- `--log-file`
- `--config <path>`
- `--no-color`
- `--quiet`
- `--version`

Global options must appear before subcommands, e.g. `ableton-cli --output json doctor`.

## JSON output envelope

Use `--output json` for machine-readable responses.

```bash
ableton-cli --output json ping
```

```json
{
  "ok": true,
  "command": "ping",
  "args": {},
    "result": {
      "host": "127.0.0.1",
      "port": 8765,
      "protocol_version": 3,
      "remote_script_version": "0.5.0",
      "rtt_ms": 2.31
    },
  "error": null
}
```

## Exit codes

- `0` success
- `2` invalid arguments
- `3` invalid configuration
- `10` Ableton not connected
- `11` Remote Script not installed or not detected
- `12` timeout
- `13` protocol mismatch
- `20` execution failure
- `99` internal error
