"""Readable names for song, scene, track-state and view settings.

These mirror the Remote Script's ``song_settings_specs`` (the Remote Script is
installed into Live separately and cannot import this package); the CLI uses
them to reject invalid input before contacting Live.
"""

from __future__ import annotations

#: Song.midi_recording_quantization, in Live's enum order.
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

#: Song.capture_midi destinations.
CAPTURE_DESTINATIONS: tuple[str, ...] = ("auto", "session", "arrangement")

#: Track.current_monitoring_state names.
MONITORING_STATES: tuple[str, ...] = ("in", "auto", "off")

#: Views accepted by ``view show``.
VIEW_NAMES: tuple[str, ...] = ("session", "arranger", "detail", "clip", "device-chain")

#: Note names -> Song.root_note (0-11); sharps and flats.
ROOT_NOTES: dict[str, int] = {
    "C": 0,
    "C#": 1,
    "DB": 1,
    "D": 2,
    "D#": 3,
    "EB": 3,
    "E": 4,
    "F": 5,
    "F#": 6,
    "GB": 6,
    "G": 7,
    "G#": 8,
    "AB": 8,
    "A": 9,
    "A#": 10,
    "BB": 10,
    "B": 11,
}

SWING_AMOUNT_MAX = 1.0
GROOVE_AMOUNT_MAX = 1.3
