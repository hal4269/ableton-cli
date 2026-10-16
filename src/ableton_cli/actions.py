from __future__ import annotations

from dataclasses import dataclass

from .command_specs import TRANSPORT_COMMAND_SPECS


@dataclass(frozen=True, slots=True)
class StableActionMapping:
    action: str
    command: str
    capability: str


def transport_action_mappings() -> tuple[StableActionMapping, ...]:
    """Action mappings derived from the transport command specs.

    The action name, CLI form and capability text already live on
    TransportSurfaceSpec; repeating them here is how the two drift apart.
    """
    return tuple(
        StableActionMapping(
            action=spec.action_name,
            command=spec.action_command,
            capability=spec.capability,
        )
        for spec in TRANSPORT_COMMAND_SPECS
        if spec.action_name is not None
        and spec.action_command is not None
        and spec.capability is not None
    )


STABLE_ACTION_MAPPINGS: tuple[StableActionMapping, ...] = (
    StableActionMapping(
        action="ping",
        command="uv run ableton-cli --output json ping",
        capability="Check connectivity and protocol metadata.",
    ),
    StableActionMapping(
        action="wait_ready",
        command="uv run ableton-cli --output json wait-ready",
        capability="Poll until Ableton Live and the Remote Script are reachable.",
    ),
    StableActionMapping(
        action="get_song_info",
        command="uv run ableton-cli --output json song info",
        capability="Read global song state such as tempo and transport status.",
    ),
    StableActionMapping(
        action="song_new",
        command="uv run ableton-cli --output json song new",
        capability="Create a new Ableton Set when supported by Live API.",
    ),
    StableActionMapping(
        action="song_undo",
        command="uv run ableton-cli --output json song undo",
        capability="Undo the most recent Ableton operation when supported by Live API.",
    ),
    StableActionMapping(
        action="song_redo",
        command="uv run ableton-cli --output json song redo",
        capability="Redo the most recently undone Ableton operation when supported by Live API.",
    ),
    StableActionMapping(
        action="song_loop_get",
        command="uv run ableton-cli --output json song loop get",
        capability="Read the Arrangement loop region (enabled, start, length, end in beats).",
    ),
    StableActionMapping(
        action="song_loop_set",
        command=(
            "uv run ableton-cli --output json song loop set [--enabled|--disabled] [--start "
            "<beats>] [--length <beats>]"
        ),
        capability="Change the Arrangement loop region.",
    ),
    StableActionMapping(
        action="song_metronome_set",
        command="uv run ableton-cli --output json song metronome set <true|false>",
        capability="Switch the metronome on or off.",
    ),
    StableActionMapping(
        action="song_swing_set",
        command="uv run ableton-cli --output json song swing set <0-1>",
        capability="Set the global swing amount.",
    ),
    StableActionMapping(
        action="song_groove_amount_set",
        command="uv run ableton-cli --output json song groove-amount set <0-1.3>",
        capability="Set the Groove Pool global amount.",
    ),
    StableActionMapping(
        action="song_scale_set",
        command=(
            "uv run ableton-cli --output json song scale set [--root <note>] [--name <scale>] "
            "[--mode|--no-mode]"
        ),
        capability="Set the song key, scale name and scale mode (Live 12+).",
    ),
    StableActionMapping(
        action="song_record_quantization_set",
        command=(
            "uv run ableton-cli --output json song record-quantization set "
            "<none|1/4|1/8|1/8t|1/8+1/8t|1/16|1/16t|1/16+1/16t|1/32>"
        ),
        capability="Set MIDI record quantization.",
    ),
    StableActionMapping(
        action="song_capture_midi",
        command=(
            "uv run ableton-cli --output json song capture-midi [--destination "
            "auto|session|arrangement]"
        ),
        capability="Capture recently played MIDI into a clip.",
    ),
    StableActionMapping(
        action="get_session_info",
        command="uv run ableton-cli --output json session info",
        capability="Read session view state and structure information.",
    ),
    StableActionMapping(
        action="get_track_info",
        command="uv run ableton-cli --output json track info --track-index <track>",
        capability="Read one track details by selector.",
    ),
    *transport_action_mappings(),
    StableActionMapping(
        action="arrangement_record_start",
        command="uv run ableton-cli --output json arrangement record start",
        capability="Start arrangement recording when supported by Live API.",
    ),
    StableActionMapping(
        action="arrangement_record_stop",
        command="uv run ableton-cli --output json arrangement record stop",
        capability="Stop arrangement recording when supported by Live API.",
    ),
    StableActionMapping(
        action="back_to_arranger",
        command="uv run ableton-cli --output json arrangement back-to-arranger",
        capability="Press Back to Arrangement so every track follows the Arrangement again.",
    ),
    StableActionMapping(
        action="list_tracks",
        command="uv run ableton-cli --output json tracks list",
        capability="List all tracks and their basic properties.",
    ),
    StableActionMapping(
        action="create_midi_track",
        command="uv run ableton-cli --output json tracks create midi [--index <index>]",
        capability="Insert a MIDI track at an index or append.",
    ),
    StableActionMapping(
        action="create_audio_track",
        command="uv run ableton-cli --output json tracks create audio [--index <index>]",
        capability="Insert an audio track at an index or append.",
    ),
    StableActionMapping(
        action="tracks_delete",
        command="uv run ableton-cli --output json tracks delete <track>",
        capability="Delete a track by index when supported by Live API.",
    ),
    StableActionMapping(
        action="tracks_duplicate",
        command="uv run ableton-cli --output json tracks duplicate <track>",
        capability="Duplicate a track; the copy is inserted right after it.",
    ),
    StableActionMapping(
        action="track_monitoring_get",
        command="uv run ableton-cli --output json track monitoring get --track-index <track>",
        capability="Read a track's monitoring state (in, auto, off).",
    ),
    StableActionMapping(
        action="track_monitoring_set",
        command=(
            "uv run ableton-cli --output json track monitoring set <in|auto|off> "
            "--track-index <track>"
        ),
        capability="Set a track's monitoring state (not on group tracks).",
    ),
    StableActionMapping(
        action="track_fold_set",
        command=(
            "uv run ableton-cli --output json track fold set <true|false> --track-index <track>"
        ),
        capability="Fold or unfold a group track.",
    ),
    StableActionMapping(
        action="set_track_color",
        command=(
            "uv run ableton-cli --output json track color set <color_index> --track-index <track>"
        ),
        capability="Set a track color (0-69, Live's color chooser).",
    ),
    StableActionMapping(
        action="set_track_name",
        command="uv run ableton-cli --output json track name set <name> --track-index <track>",
        capability="Rename a track.",
    ),
    StableActionMapping(
        action="set_track_volume",
        command="uv run ableton-cli --output json track volume set <value> --track-index <track>",
        capability="Set track volume in range 0.0 to 1.0.",
    ),
    StableActionMapping(
        action="get_track_mute",
        command="uv run ableton-cli --output json track mute get --track-index <track>",
        capability="Read track mute state.",
    ),
    StableActionMapping(
        action="set_track_mute",
        command="uv run ableton-cli --output json track mute set <value> --track-index <track>",
        capability="Update track mute state.",
    ),
    StableActionMapping(
        action="get_track_solo",
        command="uv run ableton-cli --output json track solo get --track-index <track>",
        capability="Read track solo state.",
    ),
    StableActionMapping(
        action="set_track_solo",
        command="uv run ableton-cli --output json track solo set <value> --track-index <track>",
        capability="Update track solo state.",
    ),
    StableActionMapping(
        action="get_track_arm",
        command="uv run ableton-cli --output json track arm get --track-index <track>",
        capability="Read track arm state.",
    ),
    StableActionMapping(
        action="set_track_arm",
        command="uv run ableton-cli --output json track arm set <value> --track-index <track>",
        capability="Update track arm state.",
    ),
    StableActionMapping(
        action="get_track_panning",
        command="uv run ableton-cli --output json track panning get --track-index <track>",
        capability="Read track panning value.",
    ),
    StableActionMapping(
        action="set_track_panning",
        command="uv run ableton-cli --output json track panning set <value> --track-index <track>",
        capability="Update track panning in range -1.0 to 1.0.",
    ),
    StableActionMapping(
        action="get_track_send",
        command="uv run ableton-cli --output json track send get <send> --track-index <track>",
        capability="Read one track send level by 0-based send index.",
    ),
    StableActionMapping(
        action="set_track_send",
        command=(
            "uv run ableton-cli --output json track send set <send> <value> --track-index <track>"
        ),
        capability="Update one track send level in range 0.0 to 1.0.",
    ),
    StableActionMapping(
        action="list_return_tracks",
        command="uv run ableton-cli --output json return-tracks list",
        capability="List all return tracks and their mixer state.",
    ),
    StableActionMapping(
        action="set_return_track_volume",
        command="uv run ableton-cli --output json return-track volume set <return-track> <value>",
        capability="Update one return-track volume in range 0.0 to 1.0.",
    ),
    StableActionMapping(
        action="get_master_info",
        command="uv run ableton-cli --output json master info",
        capability="Read master track name, volume, and panning.",
    ),
    StableActionMapping(
        action="list_master_devices",
        command="uv run ableton-cli --output json master devices list",
        capability="List master track devices and parameters.",
    ),
    StableActionMapping(
        action="set_mixer_crossfader",
        command="uv run ableton-cli --output json mixer crossfader set <value>",
        capability="Update mixer crossfader position in range -1.0 to 1.0.",
    ),
    StableActionMapping(
        action="set_mixer_cue_routing",
        command="uv run ableton-cli --output json mixer cue-routing set <routing>",
        capability="Update cue routing using an exact routing name.",
    ),
    StableActionMapping(
        action="get_track_routing_input",
        command="uv run ableton-cli --output json track routing input get --track-index <track>",
        capability="Read current and available input routing for one track.",
    ),
    StableActionMapping(
        action="set_track_routing_output",
        command=(
            "uv run ableton-cli --output json track routing output set --track-index <track> "
            "--type <routing-type> --channel <routing-channel>"
        ),
        capability="Update output routing using exact type and channel names.",
    ),
    StableActionMapping(
        action="create_clip",
        command="uv run ableton-cli --output json clip create <track> <clip> --length <beats>",
        capability="Create a clip in a slot with a target beat length.",
    ),
    StableActionMapping(
        action="add_notes_to_clip",
        command=(
            "uv run ableton-cli --output json clip notes add <track> <clip> (--notes-js"
            "on '<json-array>' | --notes-file <path>)"
        ),
        capability="Add MIDI notes to an existing clip slot.",
    ),
    StableActionMapping(
        action="get_clip_notes",
        command=(
            "uv run ableton-cli --output json clip notes get <track> <clip> [--start-ti"
            "me <beats>] [--end-time <beats>] [--pitch <midi>]"
        ),
        capability="Read clip notes with optional time/pitch filters.",
    ),
    StableActionMapping(
        action="clear_clip_notes",
        command=(
            "uv run ableton-cli --output json clip notes clear <track> <clip> [--start-"
            "time <beats>] [--end-time <beats>] [--pitch <midi>]"
        ),
        capability="Remove matching clip notes by optional time/pitch filters.",
    ),
    StableActionMapping(
        action="replace_clip_notes",
        command=(
            "uv run ableton-cli --output json clip notes replace <track> <clip> (--note"
            "s-json '<json-array>' | --notes-file <path>) [--start-time <beats>] [--end"
            "-time <beats>] [--pitch <midi>]"
        ),
        capability="Clear matching notes then add replacement notes.",
    ),
    StableActionMapping(
        action="update_clip_notes",
        command=(
            "uv run ableton-cli --output json clip notes update <track> <clip> (--notes"
            "-json '<json-array>' | --notes-file <path>)"
        ),
        capability=(
            "Edit existing notes in place by note_id without disturbing unrelated notes "
            "(requires Live 12+ extended note API)."
        ),
    ),
    StableActionMapping(
        action="arrangement_clip_notes_add",
        command=(
            "uv run ableton-cli --output json arrangement clip notes add <track> <index"
            "> (--notes-json '<json-array>' | --notes-file <path>)"
        ),
        capability="Add MIDI notes to an arrangement clip by list index.",
    ),
    StableActionMapping(
        action="arrangement_clip_notes_get",
        command=(
            "uv run ableton-cli --output json arrangement clip notes get <track> <index"
            "> [--start-time <beats>] [--end-time <beats>] [--pitch <midi>]"
        ),
        capability="Read arrangement clip notes with optional time/pitch filters.",
    ),
    StableActionMapping(
        action="arrangement_clip_notes_clear",
        command=(
            "uv run ableton-cli --output json arrangement clip notes clear <track> <ind"
            "ex> [--start-time <beats>] [--end-time <beats>] [--pitch <midi>]"
        ),
        capability="Remove matching arrangement clip notes by optional time/pitch filters.",
    ),
    StableActionMapping(
        action="arrangement_clip_notes_replace",
        command=(
            "uv run ableton-cli --output json arrangement clip notes replace <track> <i"
            "ndex> (--notes-json '<json-array>' | --notes-file <path>) [--start-time <b"
            "eats>] [--end-time <beats>] [--pitch <midi>]"
        ),
        capability="Clear matching arrangement notes then add replacements.",
    ),
    StableActionMapping(
        action="arrangement_clip_notes_import_browser",
        command=(
            "uv run ableton-cli --output json arrangement clip notes import-browser <tr"
            "ack> <index> <target> [--mode <replace|append>] [--import-length] [--impor"
            "t-groove]"
        ),
        capability="Import notes from a browser `.alc` item into an arrangement clip.",
    ),
    StableActionMapping(
        action="arrangement_clip_delete",
        command=(
            "uv run ableton-cli --output json arrangement clip delete <track> [index] ["
            "--start <beat> --end <beat>] [--all]"
        ),
        capability="Delete arrangement clips by index, time range, or all mode.",
    ),
    StableActionMapping(
        action="arrangement_from_session",
        command='uv run ableton-cli --output json arrangement from-session --scenes "0:24,1:48"',
        capability="Expand session scenes into Arrangement using explicit scene durations.",
    ),
    StableActionMapping(
        action="arrangement_clip_from_session",
        command=(
            "uv run ableton-cli --output json arrangement clip from-session "
            "<track> <slot> --start <beats>"
        ),
        capability=(
            "Place an exact copy of a session clip (envelopes, probability, loop) "
            "in the Arrangement."
        ),
    ),
    StableActionMapping(
        action="clip_delete",
        command="uv run ableton-cli --output json clip delete <track> <clip>",
        capability="Delete the session clip in a clip slot.",
    ),
    StableActionMapping(
        action="set_clip_color",
        command="uv run ableton-cli --output json clip color set <track> <clip> <color_index>",
        capability="Set a session clip color (0-69).",
    ),
    StableActionMapping(
        action="clip_launch_get",
        command="uv run ableton-cli --output json clip launch get <track> <clip>",
        capability="Read a session clip's launch mode, quantization, legato and velocity amount.",
    ),
    StableActionMapping(
        action="clip_launch_set",
        command=(
            "uv run ableton-cli --output json clip launch set <track> <clip> "
            "[--mode <mode>] [--quantization <q>] [--legato|--no-legato] [--velocity-amount <0-1>]"
        ),
        capability="Change a session clip's launch settings.",
    ),
    StableActionMapping(
        action="clip_crop",
        command="uv run ableton-cli --output json clip crop <track> <clip>",
        capability="Crop a session clip to its loop (or start/end markers when not looping).",
    ),
    StableActionMapping(
        action="clip_duplicate_loop",
        command="uv run ableton-cli --output json clip duplicate-loop <track> <clip>",
        capability="Double a MIDI clip's loop, copying notes and envelopes into the new half.",
    ),
    StableActionMapping(
        action="set_clip_signature",
        command=(
            "uv run ableton-cli --output json clip signature set <track> <clip> "
            "<numerator> <denominator>"
        ),
        capability="Set a session clip's time signature.",
    ),
    StableActionMapping(
        action="set_clip_mixer_envelope",
        command=(
            "uv run ableton-cli --output json clip envelope mixer set <track> <clip> "
            "<volume|panning|send> [--send-index <n>] --points-json <json>"
        ),
        capability="Write a clip envelope for the track's volume, panning or a send.",
    ),
    StableActionMapping(
        action="clip_duplicate",
        command="uv run ableton-cli --output json clip duplicate <track> <src_clip> <dst_clip>",
        capability="Duplicate a clip (exact copy, incl. envelopes) into an empty slot.",
    ),
    StableActionMapping(
        action="set_clip_name",
        command="uv run ableton-cli --output json clip name set <track> <clip> <name>",
        capability="Rename a clip.",
    ),
    StableActionMapping(
        action="fire_clip",
        command="uv run ableton-cli --output json clip fire <track> <clip>",
        capability="Launch a clip slot.",
    ),
    StableActionMapping(
        action="stop_clip",
        command="uv run ableton-cli --output json clip stop <track> <clip>",
        capability="Stop a playing clip slot.",
    ),
    StableActionMapping(
        action="list_scenes",
        command="uv run ableton-cli --output json scenes list",
        capability="List scene indexes and names.",
    ),
    StableActionMapping(
        action="create_scene",
        command="uv run ableton-cli --output json scenes create [--index <index>]",
        capability="Create a scene at an index or append.",
    ),
    StableActionMapping(
        action="set_scene_name",
        command="uv run ableton-cli --output json scenes name set <scene> <name>",
        capability="Rename a scene.",
    ),
    StableActionMapping(
        action="fire_scene",
        command="uv run ableton-cli --output json scenes fire <scene>",
        capability="Launch all clip slots on a scene row.",
    ),
    StableActionMapping(
        action="scenes_move",
        command="uv run ableton-cli --output json scenes move <from> <to>",
        capability="Move a scene from one index to another when supported by Live API.",
    ),
    StableActionMapping(
        action="scenes_duplicate",
        command="uv run ableton-cli --output json scenes duplicate <scene>",
        capability="Duplicate a scene with its clips.",
    ),
    StableActionMapping(
        action="scene_tempo_set",
        command="uv run ableton-cli --output json scenes tempo set <scene> <bpm>|--clear",
        capability="Set or clear a scene's own tempo (Live 12+).",
    ),
    StableActionMapping(
        action="scene_signature_set",
        command=(
            "uv run ableton-cli --output json scenes signature set <scene> <numerator> "
            "<denominator>|--clear"
        ),
        capability="Set or clear a scene's own time signature (Live 12+).",
    ),
    StableActionMapping(
        action="scenes_delete",
        command="uv run ableton-cli --output json scenes delete <scene>",
        capability="Delete a scene and its clips.",
    ),
    StableActionMapping(
        action="return_tracks_create",
        command="uv run ableton-cli --output json return-tracks create",
        capability="Add a return track at the end.",
    ),
    StableActionMapping(
        action="return_tracks_delete",
        command="uv run ableton-cli --output json return-tracks delete <index>",
        capability="Delete a return track.",
    ),
    StableActionMapping(
        action="locators_list",
        command="uv run ableton-cli --output json arrangement locator list",
        capability="List Arrangement locators (cue points) sorted by time.",
    ),
    StableActionMapping(
        action="locator_add",
        command="uv run ableton-cli --output json arrangement locator add <beats> [--name <name>]",
        capability="Add a named Arrangement locator (transport stopped).",
    ),
    StableActionMapping(
        action="locator_delete",
        command="uv run ableton-cli --output json arrangement locator delete <index>",
        capability="Delete an Arrangement locator (transport stopped).",
    ),
    StableActionMapping(
        action="view_show",
        command=(
            "uv run ableton-cli --output json view show <session|arranger|detail|clip|device-chain>"
        ),
        capability="Show and focus one of Live's views.",
    ),
    StableActionMapping(
        action="view_select_track",
        command="uv run ableton-cli --output json view select track <track>",
        capability="Select a track.",
    ),
    StableActionMapping(
        action="view_select_scene",
        command="uv run ableton-cli --output json view select scene <scene>",
        capability="Select a scene.",
    ),
    StableActionMapping(
        action="view_select_clip",
        command="uv run ableton-cli --output json view select clip <track> <clip>",
        capability="Highlight a clip slot and show its clip in the Detail view.",
    ),
    StableActionMapping(
        action="transport_signature_set",
        command=(
            "uv run ableton-cli --output json transport signature set <numerator> <denominator>"
        ),
        capability="Set the song time signature.",
    ),
    StableActionMapping(
        action="stop_all_clips",
        command="uv run ableton-cli --output json session stop-all-clips",
        capability="Stop all currently playing clips in Session View.",
    ),
    StableActionMapping(
        action="get_browser_tree",
        command="uv run ableton-cli --output json browser tree [category_type]",
        capability="Read browser tree by category filter.",
    ),
    StableActionMapping(
        action="get_browser_items_at_path",
        command="uv run ableton-cli --output json browser items-at-path <path>",
        capability="List browser items at a specific path.",
    ),
    StableActionMapping(
        action="get_browser_item",
        command="uv run ableton-cli --output json browser item <target>",
        capability="Get one browser item by URI or path target.",
    ),
    StableActionMapping(
        action="get_browser_categories",
        command="uv run ableton-cli --output json browser categories [category_type]",
        capability="Read available browser categories.",
    ),
    StableActionMapping(
        action="get_browser_items",
        command=(
            "uv run ableton-cli --output json browser items <path> [--item-type <all,fo"
            "lder,device,loadable>] [--limit <n>] [--offset <n>]"
        ),
        capability="List browser children with pagination and optional item-type filter.",
    ),
    StableActionMapping(
        action="search_browser_items",
        command=(
            "uv run ableton-cli --output json browser search <query> [--path <path>] [-"
            "-item-type <all,folder,device,loadable>] [--limit <n>] [--offset <n>] [--e"
            "xact] [--case-sensitive]"
        ),
        capability="Search browser items by query across categories or a subtree path.",
    ),
    StableActionMapping(
        action="load_instrument_or_effect",
        command="uv run ableton-cli --output json browser load <track> <target>",
        capability="Load a browser item by URI or path target onto a track.",
    ),
    StableActionMapping(
        action="load_drum_kit",
        command=(
            "uv run ableton-cli --output json browser load-drum-kit <track> <rack_uri> "
            "(--kit-uri <uri> | --kit-path <path>)"
        ),
        capability="Load a drum rack and an explicitly selected kit onto a track.",
    ),
    StableActionMapping(
        action="set_device_parameter",
        command=(
            "uv run ableton-cli --output json device parameter set <value> --track-index <track> "
            "--device-index <device> --parameter-index <parameter>"
        ),
        capability="Set a device parameter value by selector.",
    ),
    StableActionMapping(
        action="device_parameters_list",
        command=(
            "uv run ableton-cli --output json device parameter list --track-index "
            "<track> --device-index <device>"
        ),
        capability="List all parameters of a device, also inside rack chains via --device-ref.",
    ),
    StableActionMapping(
        action="device_delete",
        command=(
            "uv run ableton-cli --output json device delete --track-index <track> "
            "--device-index <device>"
        ),
        capability="Delete a device, also inside rack chains via --device-ref.",
    ),
    StableActionMapping(
        action="device_move",
        command=(
            "uv run ableton-cli --output json device move --to-index <index> "
            "--track-index <track> --device-index <device>"
        ),
        capability="Move a top-level device to another position on its track.",
    ),
    StableActionMapping(
        action="device_enabled_set",
        command=(
            "uv run ableton-cli --output json device enabled set <true|false> "
            "--track-index <track> --device-index <device>"
        ),
        capability="Switch a device on or off.",
    ),
    StableActionMapping(
        action="device_insert",
        command=(
            "uv run ableton-cli --output json device insert <device_name> "
            "--track-index <track> [--index <index>]"
        ),
        capability="Insert a native Live device at a position on a track (Live 12.1.10+).",
    ),
    StableActionMapping(
        action="device_chain_get",
        command=(
            "uv run ableton-cli --output json device chains get <chain> "
            "--track-index <track> --device-index <device>"
        ),
        capability="Read a rack chain's volume, panning, mute, solo and Drum Rack choke group.",
    ),
    StableActionMapping(
        action="device_chain_set",
        command=(
            "uv run ableton-cli --output json device chains set <chain> "
            "--track-index <track> --device-index <device> [--volume <0-1>] "
            "[--panning <-1..1>] [--mute|--no-mute] [--solo|--no-solo] [--choke-group <0-16>]"
        ),
        capability="Change a rack chain's mixer or Drum Rack choke group.",
    ),
    StableActionMapping(
        action="device_variations_list",
        command=(
            "uv run ableton-cli --output json device variation list "
            "--track-index <track> --device-index <device>"
        ),
        capability="Read a rack's macro variation count and selected variation.",
    ),
    StableActionMapping(
        action="device_variation_store",
        command=(
            "uv run ableton-cli --output json device variation store "
            "--track-index <track> --device-index <device>"
        ),
        capability="Store a rack's current macro values as a new variation.",
    ),
    StableActionMapping(
        action="device_variation_recall",
        command=(
            "uv run ableton-cli --output json device variation recall <variation> "
            "--track-index <track> --device-index <device>"
        ),
        capability="Select and recall a rack macro variation.",
    ),
    StableActionMapping(
        action="device_variation_delete",
        command=(
            "uv run ableton-cli --output json device variation delete <variation> "
            "--track-index <track> --device-index <device>"
        ),
        capability="Delete a rack macro variation.",
    ),
    StableActionMapping(
        action="find_synth_devices",
        command=(
            "uv run ableton-cli --output json synth find [--track <track>] [--type <wav"
            "etable|drift|meld>]"
        ),
        capability="Find supported synth devices (Wavetable, Drift, Meld).",
    ),
    StableActionMapping(
        action="list_synth_parameters",
        command=(
            "uv run ableton-cli --output json synth parameters list --track-index <track> "
            "--device-index <device>"
        ),
        capability="List synth parameters with safety metadata and stable refs.",
    ),
    StableActionMapping(
        action="set_synth_parameter_safe",
        command=(
            "uv run ableton-cli --output json synth parameter set <value> --track-index <track> "
            "--device-index <device> --parameter-index <parameter>"
        ),
        capability="Safely set a synth parameter by selector with strict range validation.",
    ),
    StableActionMapping(
        action="observe_synth_parameters",
        command=(
            "uv run ableton-cli --output json synth observe --track-index <track> "
            "--device-index <device>"
        ),
        capability="Capture one-shot synth parameter snapshot.",
    ),
    StableActionMapping(
        action="list_standard_synth_keys",
        command="uv run ableton-cli --output json synth <wavetable|drift|meld> keys",
        capability="List stable wrapper keys for a standard synth type.",
    ),
    StableActionMapping(
        action="set_standard_synth_parameter_safe",
        command=(
            "uv run ableton-cli --output json synth <wavetable|drift|meld> set <value> "
            "--track-index <track> --device-index <device> --parameter-key <key>"
        ),
        capability="Safely set a standard synth key resolved to native parameter index.",
    ),
    StableActionMapping(
        action="observe_standard_synth_state",
        command=(
            "uv run ableton-cli --output json synth <wavetable|drift|meld> observe "
            "--track-index <track> --device-index <device>"
        ),
        capability="Capture one-shot wrapper state snapshot keyed by stable synth keys.",
    ),
    StableActionMapping(
        action="find_effect_devices",
        command=(
            "uv run ableton-cli --output json effect find [--track <track>] [--type <eq"
            "8|limiter|compressor|auto_filter|reverb|utility>]"
        ),
        capability=(
            "Find supported effect devices (EQ Eight, Limiter, Compressor, Auto Filter,"
            " Reverb, Utility)."
        ),
    ),
    StableActionMapping(
        action="list_effect_parameters",
        command=(
            "uv run ableton-cli --output json effect parameters list --track-index <track> "
            "--device-index <device>"
        ),
        capability="List effect parameters with safety metadata and stable refs.",
    ),
    StableActionMapping(
        action="set_effect_parameter_safe",
        command=(
            "uv run ableton-cli --output json effect parameter set <value> --track-index <track> "
            "--device-index <device> --parameter-index <parameter>"
        ),
        capability="Safely set an effect parameter by selector with strict range validation.",
    ),
    StableActionMapping(
        action="observe_effect_parameters",
        command=(
            "uv run ableton-cli --output json effect observe --track-index <track> "
            "--device-index <device>"
        ),
        capability="Capture one-shot effect parameter snapshot.",
    ),
    StableActionMapping(
        action="list_standard_effect_keys",
        command=(
            "uv run ableton-cli --output json effect <eq8|limiter|compressor|auto-filte"
            "r|reverb|utility> keys"
        ),
        capability="List stable wrapper keys for a standard effect type.",
    ),
    StableActionMapping(
        action="set_standard_effect_parameter_safe",
        command=(
            "uv run ableton-cli --output json effect <eq8|limiter|compressor|auto-filte"
            "r|reverb|utility> set <value> --track-index <track> --device-index <device> "
            "--parameter-key <key>"
        ),
        capability="Safely set a standard effect key resolved to native parameter index.",
    ),
    StableActionMapping(
        action="observe_standard_effect_state",
        command=(
            "uv run ableton-cli --output json effect <eq8|limiter|compressor|auto-filte"
            "r|reverb|utility> observe --track-index <track> --device-index <device>"
        ),
        capability="Capture one-shot wrapper state snapshot keyed by stable effect keys.",
    ),
    StableActionMapping(
        action="audio_loudness_analyze",
        command="uv run ableton-cli --output json audio loudness analyze --path <wav>",
        capability=(
            "Analyze an offline render for LUFS, peak, RMS, crest, clipping, "
            "and DC offset; requires ffmpeg and ffprobe."
        ),
    ),
    StableActionMapping(
        action="remix_mastering_plan",
        command=(
            "uv run ableton-cli --output json remix mastering plan --project <remix_project.json>"
        ),
        capability="Generate a non-destructive master chain plan in the remix manifest.",
    ),
    StableActionMapping(
        action="remix_mastering_qa",
        command=(
            "uv run ableton-cli --output json remix mastering qa --project <remix_project.json> "
            "--render <wav>"
        ),
        capability="Validate offline render analysis and master-chain readiness against targets.",
    ),
    StableActionMapping(
        action="execute_batch",
        command=(
            "uv run ableton-cli --output json batch run (--steps-file <path> | --steps-"
            "json '<json>' | --steps-stdin)"
        ),
        capability="Execute multiple remote commands atomically from JSON input.",
    ),
)


def stable_action_names() -> tuple[str, ...]:
    return tuple(item.action for item in STABLE_ACTION_MAPPINGS)


def stable_action_command_map() -> dict[str, str]:
    return {item.action: item.command for item in STABLE_ACTION_MAPPINGS}


def stable_action_capability_map() -> dict[str, str]:
    return {item.action: item.capability for item in STABLE_ACTION_MAPPINGS}
