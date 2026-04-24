"""Unit tests for compare_deezer_playlists() (T022)."""

from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock

from playlists import CompareResult
from playlists.deezer_compare import compare_deezer_playlists
from tracks.deezer_track import DeezerTrack

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _gw_track(track_id: str, title: str = "Title", artist: str = "Artist") -> dict[str, Any]:
    return {
        "SNG_ID": track_id,
        "SNG_TITLE": title,
        "ART_NAME": artist,
        "ALB_TITLE": "Album",
        "DURATION": "200",
        "TRACK_NUMBER": "1",
    }


def _local_track(deezer_ref: str | None) -> MagicMock:
    lt = MagicMock()
    lt.service_ref.return_value = deezer_ref
    lt.display_artist = "Artist"
    lt.title = "Title"
    return lt


def _playlist_with(tracks: list[Any]) -> MagicMock:
    pl = MagicMock()
    pl.tracks = tracks
    return pl


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestCompareDeezerPlaylists:
    def test_track_only_in_local_appears_in_source_only(self) -> None:
        local_track = _local_track(None)  # no DEEZER ref
        local_pl = _playlist_with([local_track])
        deezer_pl = _playlist_with([DeezerTrack(_gw_track("1"))])

        result = compare_deezer_playlists(local_pl, deezer_pl)

        assert local_track in result.source_only
        assert len(result.target_only) == 1

    def test_track_only_in_deezer_appears_in_target_only(self) -> None:
        deezer_track_1 = DeezerTrack(_gw_track("1"))
        deezer_track_2 = DeezerTrack(_gw_track("2"))
        local_track = _local_track("https://www.deezer.com/track/1")
        local_pl = _playlist_with([local_track])
        deezer_pl = _playlist_with([deezer_track_1, deezer_track_2])

        result = compare_deezer_playlists(local_pl, deezer_pl)

        assert len(result.source_only) == 0
        target_ids = [t.track_id for t in result.target_only]
        assert "2" in target_ids

    def test_identical_playlists_return_no_differences(self) -> None:
        local_track = _local_track("https://www.deezer.com/track/42")
        deezer_track = DeezerTrack(_gw_track("42"))
        local_pl = _playlist_with([local_track])
        deezer_pl = _playlist_with([deezer_track])

        result = compare_deezer_playlists(local_pl, deezer_pl)

        assert len(result.source_only) == 0
        assert len(result.target_only) == 0

    def test_return_type_is_compare_result(self) -> None:
        local_pl = _playlist_with([])
        deezer_pl = _playlist_with([])

        result = compare_deezer_playlists(local_pl, deezer_pl)

        assert isinstance(result, CompareResult)
