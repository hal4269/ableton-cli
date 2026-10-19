from __future__ import annotations

import json


def test_compact_reduces_large_json_arrays(runner, cli_app, monkeypatch) -> None:
    from ableton_cli.commands import tracks

    class _ClientStub:
        def tracks_list(self):  # noqa: ANN201
            return {
                "tracks": [
                    {
                        "index": index,
                        "stable_ref": f"track:{index}",
                        "name": f"Track {index}",
                        "mute": False,
                        "solo": False,
                        "arm": False,
                        "volume": 0.75,
                        "is_foldable": False,
                        "fold_state": None,
                        "is_grouped": False,
                        "group_track": None,
                    }
                    for index in range(40)
                ]
            }

    monkeypatch.setattr(tracks, "get_client", lambda _ctx: _ClientStub())

    result = runner.invoke(
        cli_app,
        ["--output", "json", "--compact", "tracks", "list"],
    )

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["ok"] is True
    compacted_tracks = payload["result"]["tracks"]
    assert isinstance(compacted_tracks, dict)
    assert "_compact_ref" in compacted_tracks
    assert "_compact_summary" in compacted_tracks
    ref = compacted_tracks["_compact_ref"]
    assert payload["compact_refs"][ref]["count"] == 40


def test_compact_keeps_small_arrays_unmodified(runner, cli_app, monkeypatch) -> None:
    from ableton_cli.commands import tracks

    class _ClientStub:
        def tracks_list(self):  # noqa: ANN201
            return {
                "tracks": [
                    {
                        "index": 0,
                        "stable_ref": "track:0",
                        "name": "Only",
                        "mute": False,
                        "solo": False,
                        "arm": False,
                        "volume": 0.75,
                        "is_foldable": False,
                        "fold_state": None,
                        "is_grouped": False,
                        "group_track": None,
                    }
                ]
            }

    monkeypatch.setattr(tracks, "get_client", lambda _ctx: _ClientStub())

    result = runner.invoke(
        cli_app,
        ["--output", "json", "--compact", "tracks", "list"],
    )

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["ok"] is True
    assert isinstance(payload["result"]["tracks"], list)
    assert "compact_refs" not in payload
