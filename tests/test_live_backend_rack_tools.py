"""Readable parameter values, rack chain mixer/choke, macro variations, device insert."""

from __future__ import annotations

from typing import Any

import pytest
from test_live_backend import _Chain, _Device, _Parameter, _SurfaceStub, _Track

from remote_script.AbletonCliRemote.command_backend import CommandError, dispatch_command
from remote_script.AbletonCliRemote.live_backend import LiveBackend


def _backend_with_devices(*devices: _Device) -> LiveBackend:
    backend = LiveBackend(_SurfaceStub())
    backend.context._track_at(0).devices = list(devices)
    return backend


def _rack_args(device: int = 0) -> dict[str, Any]:
    return {
        "track_ref": {"mode": "index", "index": 0},
        "device_ref": {"mode": "index", "index": device},
    }


def _rack(chains: list[Any], *, drum: bool = False) -> _Device:
    return _Device(
        "Rack",
        "DrumGroupDevice" if drum else "AudioEffectGroupDevice",
        [_Parameter("Macro 1", 0.0, max=127.0, original_name="Macro 1")],
        can_have_chains=True,
        can_have_drum_pads=drum,
        chains=chains,
    )


class _DrumChain(_Chain):
    """Drum Rack chain (Live 12): in_note plus a settable choke_group (0 = none)."""

    def __init__(self, name: str, in_note: int, choke_group: int = 0) -> None:
        _Chain.__init__(self, name)
        self.in_note = in_note
        self.choke_group = choke_group


# --- 1. Readable parameter values ---------------------------------------------------


def test_device_parameters_list_includes_display_value_and_value_items() -> None:
    device = _Device(
        "Saturator",
        "Saturator",
        [
            _Parameter("Drive", 0.25, max=1.0),
            _Parameter(
                "Type",
                1.0,
                max=2.0,
                is_quantized=True,
                value_items=("Analog Clip", "Soft Sine", "Medium Curve"),
            ),
        ],
    )
    backend = _backend_with_devices(device)

    parameters = dispatch_command(backend, "device_parameters_list", _rack_args())["parameters"]

    assert parameters[0]["display_value"] == "0.25"
    assert parameters[0]["value_items"] == []
    assert parameters[1]["display_value"] == "Soft Sine"
    assert parameters[1]["value_items"] == ["Analog Clip", "Soft Sine", "Medium Curve"]


def test_track_info_device_parameters_include_display_value() -> None:
    device = _Device(
        "Simpler", "OriginalSimpler", [_Parameter("Mode", 0.0, value_items=("Classic", "1-Shot"))]
    )
    backend = _backend_with_devices(device)

    info = backend.get_track_info(0)

    assert info["devices"][0]["parameters"][0]["display_value"] == "Classic"


# --- 2. Rack chain mixer + choke ------------------------------------------------------


def test_device_chains_list_includes_chain_mixer_and_choke_group() -> None:
    kick = _DrumChain("Kick", in_note=36)
    open_hat = _DrumChain("Open Hat", in_note=46, choke_group=1)
    open_hat.mixer_device.volume.value = 0.5
    open_hat.mute = True
    backend = _backend_with_devices(_rack([kick, open_hat], drum=True))

    chains = backend.device_chains_list(0, 0)["chains"]

    assert chains[1]["volume"] == 0.5
    assert chains[1]["volume_display"] == "0.50"
    assert chains[1]["panning"] == 0.0
    assert chains[1]["mute"] is True
    assert chains[1]["solo"] is False
    assert chains[1]["choke_group"] == 1
    assert chains[0]["choke_group"] == 0


def test_device_chains_list_reports_no_choke_group_for_other_racks() -> None:
    backend = _backend_with_devices(_rack([_Chain("Chain 1")]))

    assert backend.device_chains_list(0, 0)["chains"][0]["choke_group"] is None


def test_device_chain_get_returns_one_chain() -> None:
    backend = _backend_with_devices(_rack([_Chain("A"), _Chain("B")]))

    result = dispatch_command(backend, "device_chain_get", {**_rack_args(), "chain_index": 1})

    assert result["chain"] == 1
    assert result["name"] == "B"
    assert result["volume"] == 0.85


def test_device_chain_set_changes_only_given_settings() -> None:
    hat = _DrumChain("Closed Hat", in_note=42)
    backend = _backend_with_devices(_rack([hat], drum=True))

    result = dispatch_command(
        backend,
        "device_chain_set",
        {
            **_rack_args(),
            "chain_index": 0,
            "settings": {"volume": 0.6, "panning": -0.25, "solo": True, "choke_group": 1},
        },
    )

    assert hat.mixer_device.volume.value == 0.6
    assert hat.mixer_device.panning.value == -0.25
    assert hat.solo is True
    assert hat.mute is False
    assert hat.choke_group == 1
    assert result["choke_group"] == 1
    assert result["panning"] == -0.25


def test_device_chain_set_reaches_a_rack_inside_a_rack_chain() -> None:
    inner_chain = _Chain("Inner")
    inner_rack = _rack([inner_chain])
    backend = _backend_with_devices(_rack([_Chain("Outer", devices=[inner_rack])]))
    inner_ref = backend.device_chains_list(0, 0)["chains"][0]["devices"][0]["stable_ref"]

    dispatch_command(
        backend,
        "device_chain_set",
        {
            "track_ref": {"mode": "index", "index": 0},
            "device_ref": {"mode": "stable_ref", "stable_ref": inner_ref},
            "chain_index": 0,
            "settings": {"mute": True},
        },
    )

    assert inner_chain.mute is True


@pytest.mark.parametrize(
    "settings",
    [
        {},
        {"volume": 1.5},
        {"panning": -2.0},
        {"choke_group": 17},
        {"color": 3},
    ],
)
def test_device_chain_set_rejects_invalid_settings(settings: dict[str, Any]) -> None:
    hat = _DrumChain("Hat", in_note=42)
    backend = _backend_with_devices(_rack([hat], drum=True))

    with pytest.raises(CommandError) as exc_info:
        dispatch_command(
            backend, "device_chain_set", {**_rack_args(), "chain_index": 0, "settings": settings}
        )

    assert exc_info.value.code == "INVALID_ARGUMENT"
    assert hat.mixer_device.volume.value == 0.85


def test_device_chain_set_validates_everything_before_changing_anything() -> None:
    hat = _DrumChain("Hat", in_note=42)
    backend = _backend_with_devices(_rack([hat], drum=True))

    with pytest.raises(CommandError):
        dispatch_command(
            backend,
            "device_chain_set",
            {**_rack_args(), "chain_index": 0, "settings": {"mute": True, "volume": 3.0}},
        )

    assert hat.mute is False


def test_device_chain_set_choke_group_requires_a_drum_rack() -> None:
    backend = _backend_with_devices(_rack([_Chain("Chain 1")]))

    with pytest.raises(CommandError) as exc_info:
        dispatch_command(
            backend,
            "device_chain_set",
            {**_rack_args(), "chain_index": 0, "settings": {"choke_group": 1}},
        )

    assert exc_info.value.code == "INVALID_ARGUMENT"
    assert "Drum Rack" in exc_info.value.message


def test_device_chain_set_choke_group_not_supported_without_live_api() -> None:
    # A Drum Rack whose chains lack choke_group: an older Live API.
    backend = _backend_with_devices(_rack([_Chain("Pad")], drum=True))

    with pytest.raises(CommandError) as exc_info:
        dispatch_command(
            backend,
            "device_chain_set",
            {**_rack_args(), "chain_index": 0, "settings": {"choke_group": 1}},
        )

    assert exc_info.value.details == {"reason": "not_supported_by_live_api"}


def test_device_chain_get_rejects_out_of_range_chain() -> None:
    backend = _backend_with_devices(_rack([_Chain("A")]))

    with pytest.raises(CommandError) as exc_info:
        dispatch_command(backend, "device_chain_get", {**_rack_args(), "chain_index": 1})

    assert exc_info.value.code == "INVALID_ARGUMENT"


# --- 3. Rack macro variations ---------------------------------------------------------


class _VariationRack(_Device):
    """RackDevice with Live's macro variation API."""

    def __init__(self, variations: int = 0) -> None:
        _Device.__init__(
            self,
            "Rack",
            "InstrumentGroupDevice",
            [_Parameter("Macro 1", 0.0, max=127.0, original_name="Macro 1")],
            can_have_chains=True,
        )
        self.variations = [{"Macro 1": float(index)} for index in range(variations)]
        self.selected_variation_index = -1 if variations == 0 else 0
        self.recalled: list[int] = []

    @property
    def variation_count(self) -> int:
        return len(self.variations)

    def store_variation(self) -> None:
        self.variations.append({"Macro 1": self.parameters[0].value})
        self.selected_variation_index = len(self.variations) - 1

    def recall_selected_variation(self) -> None:
        self.recalled.append(self.selected_variation_index)
        self.parameters[0].value = self.variations[self.selected_variation_index]["Macro 1"]

    def delete_selected_variation(self) -> None:
        del self.variations[self.selected_variation_index]
        self.selected_variation_index = min(self.selected_variation_index, len(self.variations) - 1)


def test_device_variations_list_reports_count_and_selection() -> None:
    backend = _backend_with_devices(_VariationRack(variations=3))

    result = dispatch_command(backend, "device_variations_list", _rack_args())

    assert result == {"track": 0, "device": 0, "variation_count": 3, "selected_variation_index": 0}


def test_device_variation_store_recall_delete() -> None:
    rack = _VariationRack(variations=2)
    backend = _backend_with_devices(rack)
    rack.parameters[0].value = 99.0

    stored = dispatch_command(backend, "device_variation_store", _rack_args())
    recalled = dispatch_command(
        backend, "device_variation_recall", {**_rack_args(), "variation_index": 1}
    )
    deleted = dispatch_command(
        backend, "device_variation_delete", {**_rack_args(), "variation_index": 0}
    )

    assert stored["variation_count"] == 3
    assert recalled["selected_variation_index"] == 1
    assert rack.recalled == [1]
    assert rack.parameters[0].value == 1.0
    assert deleted["variation_count"] == 2


@pytest.mark.parametrize("command", ["device_variation_recall", "device_variation_delete"])
def test_device_variation_index_must_exist(command: str) -> None:
    backend = _backend_with_devices(_VariationRack(variations=2))

    with pytest.raises(CommandError) as exc_info:
        dispatch_command(backend, command, {**_rack_args(), "variation_index": 2})

    assert exc_info.value.code == "INVALID_ARGUMENT"


def test_device_variations_not_supported_without_live_api() -> None:
    backend = _backend_with_devices(_rack([]))

    with pytest.raises(CommandError) as exc_info:
        dispatch_command(backend, "device_variations_list", _rack_args())

    assert exc_info.value.details == {"reason": "not_supported_by_live_api"}


def test_device_variations_reject_non_rack_device() -> None:
    backend = _backend_with_devices(_Device("Echo", "Echo", []))

    with pytest.raises(CommandError) as exc_info:
        dispatch_command(backend, "device_variations_list", _rack_args())

    assert exc_info.value.code == "INVALID_ARGUMENT"
    assert exc_info.value.details is None


# --- 4. Device insert -----------------------------------------------------------------

_NATIVE_DEVICES = {"Saturator": "Saturator", "EQ Eight": "Eq8", "Utility": "StereoGain"}


class _InsertTrack(_Track):
    """Track with Live 12's Track.insert_device(device_name, target_index)."""

    def __init__(self) -> None:
        super().__init__(name="Lead", has_audio_input=False, has_midi_input=True)
        self.devices = [
            _Device("Wavetable", "InstrumentVector", []),
            _Device("Echo", "Echo", []),
        ]

    def insert_device(self, device_name: str, target_index: int) -> _Device:
        if device_name not in _NATIVE_DEVICES:
            raise RuntimeError(f"Device not found: {device_name}")
        device = _Device(device_name, _NATIVE_DEVICES[device_name], [])
        self.devices.insert(target_index, device)
        return device


def _backend_with_insert_track() -> tuple[LiveBackend, _InsertTrack]:
    surface = _SurfaceStub()
    track = _InsertTrack()
    surface.song().tracks[0] = track
    return LiveBackend(surface), track


def _insert_args(name: str, index: int | None) -> dict[str, Any]:
    return {"track_ref": {"mode": "index", "index": 0}, "device_name": name, "index": index}


def test_device_insert_places_native_device_at_index() -> None:
    backend, track = _backend_with_insert_track()

    result = dispatch_command(backend, "device_insert", _insert_args("Saturator", 1))

    assert [device.name for device in track.devices] == ["Wavetable", "Saturator", "Echo"]
    assert result["index"] == 1
    assert result["device_name"] == "Saturator"
    assert [device["name"] for device in result["devices"]] == ["Wavetable", "Saturator", "Echo"]


def test_device_insert_without_index_appends() -> None:
    backend, track = _backend_with_insert_track()

    result = dispatch_command(backend, "device_insert", _insert_args("Utility", None))

    assert track.devices[-1].name == "Utility"
    assert result["index"] == 2


def test_device_insert_rejects_out_of_range_index() -> None:
    backend, track = _backend_with_insert_track()

    with pytest.raises(CommandError) as exc_info:
        dispatch_command(backend, "device_insert", _insert_args("Utility", 3))

    assert exc_info.value.code == "INVALID_ARGUMENT"
    assert len(track.devices) == 2


def test_device_insert_reports_unknown_device_name() -> None:
    backend, _track = _backend_with_insert_track()

    with pytest.raises(CommandError) as exc_info:
        dispatch_command(backend, "device_insert", _insert_args("Serum", 0))

    assert exc_info.value.code == "INVALID_ARGUMENT"
    assert "Serum" in exc_info.value.message


def test_device_insert_not_supported_without_live_api() -> None:
    backend = LiveBackend(_SurfaceStub())

    with pytest.raises(CommandError) as exc_info:
        dispatch_command(backend, "device_insert", _insert_args("Utility", 0))

    assert exc_info.value.details == {"reason": "not_supported_by_live_api"}
