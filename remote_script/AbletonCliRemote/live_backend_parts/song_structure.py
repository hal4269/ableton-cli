from __future__ import annotations

from typing import Any

from .base import _invalid_argument, _not_supported_by_live_api

#: Two cue points closer than this (in beats) are treated as the same position.
_CUE_TIME_TOLERANCE = 1e-6


class LiveBackendSongStructureMixin:
    """Song layout: duplicating/deleting tracks and scenes, return tracks,
    Arrangement locators (cue points) and the time signature."""

    def _song_function(self, name: str) -> Any:
        function = getattr(self._ctx._song(), name, None)
        if not callable(function):
            raise _not_supported_by_live_api(
                message=f"Song.{name} is not available in Live API",
                hint=f"Use a Live version exposing song.{name} (Live 12+).",
            )
        return function

    def tracks_duplicate(self, track: int) -> dict[str, Any]:
        self._ctx._track_at(track)
        self._song_function("duplicate_track")(track)
        duplicate = self._ctx._track_at(track + 1)
        return {
            "track": track,
            "new_track": track + 1,
            "name": str(getattr(duplicate, "name", "")),
            "track_count": len(list(self._ctx._song().tracks)),
        }

    def scenes_duplicate(self, scene: int) -> dict[str, Any]:
        self._ctx._scene_at(scene)
        self._song_function("duplicate_scene")(scene)
        return {
            "scene": scene,
            "new_scene": scene + 1,
            "scene_count": len(list(self._ctx._song().scenes)),
        }

    def scenes_delete(self, scene: int) -> dict[str, Any]:
        self._ctx._scene_at(scene)
        self._song_function("delete_scene")(scene)
        return {
            "scene": scene,
            "deleted": True,
            "scene_count": len(list(self._ctx._song().scenes)),
        }

    def return_tracks_create(self) -> dict[str, Any]:
        self._song_function("create_return_track")()
        return_tracks = list(self._ctx._song().return_tracks)
        created = return_tracks[-1]
        return {
            "index": len(return_tracks) - 1,
            "name": str(getattr(created, "name", "")),
            "return_track_count": len(return_tracks),
        }

    def return_tracks_delete(self, index: int) -> dict[str, Any]:
        self._ctx._return_track_at(index)
        self._song_function("delete_return_track")(index)
        return {
            "index": index,
            "deleted": True,
            "return_track_count": len(list(self._ctx._song().return_tracks)),
        }

    def _cue_points(self) -> list[Any]:
        cue_points = getattr(self._ctx._song(), "cue_points", None)
        if cue_points is None:
            raise _not_supported_by_live_api(
                message="Song.cue_points is not available in Live API",
                hint="Use a Live version exposing song.cue_points (Live 12+).",
            )
        return sorted(cue_points, key=lambda cue: float(cue.time))

    def _cue_at(self, time: float) -> Any | None:
        for cue in self._cue_points():
            if abs(float(cue.time) - time) < _CUE_TIME_TOLERANCE:
                return cue
        return None

    def _toggle_cue_at(self, time: float) -> None:
        """Live only toggles a cue at the playback position; restore it afterwards."""
        song = self._ctx._song()
        set_or_delete_cue = self._song_function("set_or_delete_cue")
        previous_time = float(song.current_song_time)
        song.current_song_time = time
        try:
            set_or_delete_cue()
        finally:
            song.current_song_time = previous_time

    def locators_list(self) -> dict[str, Any]:
        locators = [
            {"index": index, "name": str(cue.name), "time": float(cue.time)}
            for index, cue in enumerate(self._cue_points())
        ]
        return {"locator_count": len(locators), "locators": locators}

    def locator_add(self, time: float, name: str | None) -> dict[str, Any]:
        if self._cue_at(time) is not None:
            raise _invalid_argument(
                message=f"A locator already exists at beat {time}",
                hint="Use 'arrangement locator list' and pick a free position.",
            )
        if bool(getattr(self._ctx._song(), "is_playing", False)):
            raise _invalid_argument(
                message="Cannot add a locator while the transport is playing",
                hint="Stop the transport first ('transport stop').",
            )
        self._toggle_cue_at(time)
        cue = self._cue_at(time)
        if cue is None:
            raise _invalid_argument(
                message=f"Live did not create a locator at beat {time}",
                hint="Check that the position lies inside the Arrangement.",
            )
        if name is not None:
            cue.name = name
        index = next(i for i, item in enumerate(self._cue_points()) if item is cue)
        return {"index": index, "name": str(cue.name), "time": float(cue.time)}

    def locator_delete(self, index: int) -> dict[str, Any]:
        cue_points = self._cue_points()
        if index < 0 or index >= len(cue_points):
            raise _invalid_argument(
                message=f"locator out of range: {index}",
                hint="Use an index from 'arrangement locator list'.",
            )
        if bool(getattr(self._ctx._song(), "is_playing", False)):
            raise _invalid_argument(
                message="Cannot delete a locator while the transport is playing",
                hint="Stop the transport first ('transport stop').",
            )
        cue = cue_points[index]
        time = float(cue.time)
        name = str(cue.name)
        self._toggle_cue_at(time)
        return {"index": index, "name": name, "time": time, "deleted": True}

    def transport_signature_set(self, numerator: int, denominator: int) -> dict[str, Any]:
        song = self._ctx._song()
        song.signature_numerator = numerator
        song.signature_denominator = denominator
        return {
            "numerator": int(song.signature_numerator),
            "denominator": int(song.signature_denominator),
        }
