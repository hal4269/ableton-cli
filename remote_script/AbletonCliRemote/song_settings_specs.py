"""Name tables for song settings, scene settings, track state and view commands.

The wire protocol carries readable names; these tables map them to the
integer values and view names of the Live Object Model (Live 12+).
"""

from __future__ import annotations

#: Song.midi_recording_quantization (Live.Song.RecordingQuantization), by value.
RECORD_QUANTIZATION_NAMES: tuple[str, ...] = (
    "none",
    "1/4",
    "1/8",
    "1/8t",
    "1/8+1/8t",
    "1/16",
    "1/16t",
    "1/16+1/16t",
    "1/32",
)

#: Song.capture_midi(destination): 0 auto, 1 Session, 2 Arrangement.
CAPTURE_DESTINATIONS: tuple[str, ...] = ("auto", "session", "arrangement")

#: Track.current_monitoring_state: 0 In, 1 Auto, 2 Off.
MONITORING_STATES: tuple[str, ...] = ("in", "auto", "off")

#: Song.root_note (0-11) as note names.
ROOT_NOTE_NAMES: tuple[str, ...] = (
    "C",
    "C#",
    "D",
    "D#",
    "E",
    "F",
    "F#",
    "G",
    "G#",
    "A",
    "A#",
    "B",
)

#: CLI view name -> Application.View view name.
LIVE_VIEW_NAMES: dict[str, str] = {
    "session": "Session",
    "arranger": "Arranger",
    "detail": "Detail",
    "clip": "Detail/Clip",
    "device-chain": "Detail/DeviceChain",
}

#: Song.swing_amount range.
SWING_AMOUNT_MAX = 1.0
#: Song.groove_amount range (the Groove Pool's global amount goes up to 130%).
GROOVE_AMOUNT_MAX = 1.3
