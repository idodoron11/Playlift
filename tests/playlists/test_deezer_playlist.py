"""Unit tests for DeezerPlaylist.

Covers T011 (create, tracks, add_tracks, import_tracks, create_from_another_playlist,
track_matcher) and T017 (remove_track, sync_tracks, sort-tracks).
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, cast
from unittest.mock import MagicMock, patch

from playlists.deezer_playlist import DeezerPlaylist
from tracks.deezer_track import DeezerTrack

if TYPE_CHECKING:
    from tracks import Track

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


def _make_dz(track_list: list[dict[str, Any]] | None = None) -> MagicMock:
    dz = MagicMock()
    dz.gw.get_playlist_tracks.return_value = track_list or []
    dz.gw.create_playlist.return_value = 99999
    return dz


# ---------------------------------------------------------------------------
# T011: create() classmethod
# ---------------------------------------------------------------------------


class TestDeezerPlaylistCreate:
    def test_create_returns_deezer_playlist_instance(self) -> None:
        dz = _make_dz()
        playlist = DeezerPlaylist.create("My Playlist", deezer=dz)

        assert isinstance(playlist, DeezerPlaylist)
        dz.gw.create_playlist.assert_called_once()

    def test_create_uses_returned_id(self) -> None:
        dz = _make_dz()
        dz.gw.create_playlist.return_value = 42
        playlist = DeezerPlaylist.create("My Playlist", deezer=dz)

        assert playlist.playlist_id == "42"

    def test_create_public_passes_status_zero(self) -> None:
        dz = _make_dz()
        DeezerPlaylist.create("Public", public=True, deezer=dz)

        _, kwargs = dz.gw.create_playlist.call_args
        assert kwargs.get("status") == 0 or dz.gw.create_playlist.call_args[0][1] == 0  # positional or keyword

    def test_create_private_passes_status_one(self) -> None:
        dz = _make_dz()
        DeezerPlaylist.create("Private", public=False, deezer=dz)

        _, kwargs = dz.gw.create_playlist.call_args
        assert kwargs.get("status") == 1 or dz.gw.create_playlist.call_args[0][1] == 1


# ---------------------------------------------------------------------------
# T011: tracks property (lazy-load + cache)
# ---------------------------------------------------------------------------


class TestDeezerPlaylistTracks:
    def test_tracks_lazy_loads_via_gw(self) -> None:
        dz = _make_dz([_gw_track("1"), _gw_track("2")])
        playlist = DeezerPlaylist("123", deezer=dz)

        tracks = playlist.tracks

        assert len(tracks) == 2
        dz.gw.get_playlist_tracks.assert_called_once_with("123")

    def test_tracks_caches_after_first_load(self) -> None:
        dz = _make_dz([_gw_track("1")])
        playlist = DeezerPlaylist("123", deezer=dz)

        _ = playlist.tracks
        _ = playlist.tracks

        dz.gw.get_playlist_tracks.assert_called_once()


# ---------------------------------------------------------------------------
# T011: add_tracks() invalidates cache
# ---------------------------------------------------------------------------


class TestDeezerPlaylistAddTracks:
    def test_add_tracks_calls_gw_add(self) -> None:
        dz = _make_dz()
        playlist = DeezerPlaylist("123", deezer=dz)
        t1 = DeezerTrack(_gw_track("1"))
        t2 = DeezerTrack(_gw_track("2"))

        playlist.add_tracks([t1, t2])

        dz.gw.add_songs_to_playlist.assert_called_once_with("123", ["1", "2"])

    def test_add_tracks_skips_tracks_already_in_playlist(self) -> None:
        # Regression: Deezer GW rejects the entire batch with ERROR_DATA_EXISTS
        # if any submitted track_id already exists in the playlist.
        dz = _make_dz([_gw_track("1")])
        playlist = DeezerPlaylist("123", deezer=dz)

        playlist.add_tracks([DeezerTrack(_gw_track("1")), DeezerTrack(_gw_track("2"))])

        dz.gw.add_songs_to_playlist.assert_called_once_with("123", ["2"])

    def test_add_tracks_skips_intra_batch_duplicates(self) -> None:
        # Regression: duplicate track_ids within the submitted list also trigger
        # ERROR_DATA_EXISTS on the Deezer GW API.
        dz = _make_dz()
        playlist = DeezerPlaylist("123", deezer=dz)

        playlist.add_tracks([DeezerTrack(_gw_track("1")), DeezerTrack(_gw_track("1"))])

        dz.gw.add_songs_to_playlist.assert_called_once_with("123", ["1"])

    def test_add_tracks_does_nothing_when_all_already_present(self) -> None:
        # Regression: if every track is already in the playlist, no API call
        # should be made (previously would call with an empty list or raise).
        dz = _make_dz([_gw_track("1")])
        playlist = DeezerPlaylist("123", deezer=dz)

        playlist.add_tracks([DeezerTrack(_gw_track("1"))])

        dz.gw.add_songs_to_playlist.assert_not_called()

    def test_add_tracks_invalidates_cache(self) -> None:
        dz = _make_dz([_gw_track("1")])
        playlist = DeezerPlaylist("123", deezer=dz)
        _ = playlist.tracks  # populate cache

        playlist.add_tracks([DeezerTrack(_gw_track("2"))])

        # cache cleared — next access should re-fetch from the API
        _ = playlist.tracks
        assert dz.gw.get_playlist_tracks.call_count == 2

    def test_add_tracks_splits_large_batch_into_chunks(self) -> None:
        from playlists.deezer_playlist import _ADD_TRACKS_CHUNK_SIZE

        dz = _make_dz()
        playlist = DeezerPlaylist("123", deezer=dz)
        tracks = cast("list[Track]", [DeezerTrack(_gw_track(str(i))) for i in range(_ADD_TRACKS_CHUNK_SIZE + 1)])

        playlist.add_tracks(tracks)

        assert dz.gw.add_songs_to_playlist.call_count == 2
        first_batch = dz.gw.add_songs_to_playlist.call_args_list[0][0][1]
        second_batch = dz.gw.add_songs_to_playlist.call_args_list[1][0][1]
        assert len(first_batch) == _ADD_TRACKS_CHUNK_SIZE
        assert len(second_batch) == 1


# ---------------------------------------------------------------------------
# T017: remove_track() invalidates cache
# ---------------------------------------------------------------------------


class TestDeezerPlaylistRemoveTrack:
    def test_remove_track_calls_gw_remove(self) -> None:
        dz = _make_dz()
        playlist = DeezerPlaylist("123", deezer=dz)
        t1 = DeezerTrack(_gw_track("1"))

        playlist.remove_track([t1])

        dz.gw.remove_songs_from_playlist.assert_called_once_with("123", ["1"])

    def test_remove_track_updates_cache_without_refetch(self) -> None:
        dz = _make_dz([_gw_track("1"), _gw_track("2")])
        playlist = DeezerPlaylist("123", deezer=dz)
        _ = playlist.tracks  # populate cache

        playlist.remove_track([DeezerTrack(_gw_track("1"))])

        assert [t.track_id for t in playlist.tracks] == ["2"]
        assert dz.gw.get_playlist_tracks.call_count == 1  # no re-fetch


# ---------------------------------------------------------------------------
# T017: sync_tracks()
# ---------------------------------------------------------------------------


class TestDeezerPlaylistSyncTracks:
    def _make_playlist_with_tracks(self, existing_ids: list[str]) -> tuple[DeezerPlaylist, MagicMock]:
        dz = _make_dz([_gw_track(i) for i in existing_ids])
        playlist = DeezerPlaylist("123", deezer=dz)
        return playlist, dz

    def test_sync_adds_missing_tracks(self) -> None:
        playlist, dz = self._make_playlist_with_tracks(["1"])
        new_track = DeezerTrack(_gw_track("2"))

        with patch.object(DeezerPlaylist, "track_matcher") as mock_matcher:
            mock_matcher.return_value.match_list.return_value = [DeezerTrack(_gw_track("1")), new_track]
            playlist.sync_tracks([], autopilot=True)

        dz.gw.add_songs_to_playlist.assert_called_once()

    def test_sync_removes_extra_tracks(self) -> None:
        playlist, dz = self._make_playlist_with_tracks(["1", "2"])

        with patch.object(DeezerPlaylist, "track_matcher") as mock_matcher:
            mock_matcher.return_value.match_list.return_value = [DeezerTrack(_gw_track("1"))]
            playlist.sync_tracks([], autopilot=True)

        dz.gw.remove_songs_from_playlist.assert_called_once()

    def test_sync_already_up_to_date_makes_no_add_remove_calls(self) -> None:
        playlist, dz = self._make_playlist_with_tracks(["1", "2"])

        with patch.object(DeezerPlaylist, "track_matcher") as mock_matcher:
            mock_matcher.return_value.match_list.return_value = [
                DeezerTrack(_gw_track("1")),
                DeezerTrack(_gw_track("2")),
            ]
            playlist.sync_tracks([], autopilot=True)

        dz.gw.add_songs_to_playlist.assert_not_called()
        dz.gw.remove_songs_from_playlist.assert_not_called()

    def test_sync_with_sort_tracks_adds_tracks_sorted_by_id(self) -> None:
        # Playlist has same tracks as resolved — no diff-step add/remove.
        # sort_tracks should clear and re-add in track_id order.
        dz = _make_dz([_gw_track("3"), _gw_track("1"), _gw_track("2")])
        playlist = DeezerPlaylist("123", deezer=dz)
        resolved = [DeezerTrack(_gw_track("3")), DeezerTrack(_gw_track("1")), DeezerTrack(_gw_track("2"))]

        with patch.object(DeezerPlaylist, "track_matcher") as mock_matcher:
            mock_matcher.return_value.match_list.return_value = resolved
            playlist.sync_tracks([], sort_tracks=True)

        add_ids = dz.gw.add_songs_to_playlist.call_args[0][1]
        assert add_ids == ["1", "2", "3"]


# ---------------------------------------------------------------------------
# T011: import_tracks()
# ---------------------------------------------------------------------------


class TestDeezerPlaylistImportTracks:
    def test_import_tracks_resolves_and_adds(self) -> None:
        dz = _make_dz()
        playlist = DeezerPlaylist("123", deezer=dz)
        matched_track = DeezerTrack(_gw_track("42"))

        with patch.object(DeezerPlaylist, "track_matcher") as mock_matcher:
            mock_matcher.return_value.match_list.return_value = [matched_track]
            playlist.import_tracks([MagicMock()])

        dz.gw.add_songs_to_playlist.assert_called_once_with("123", ["42"])


# ---------------------------------------------------------------------------
# T011: create_from_another_playlist()
# ---------------------------------------------------------------------------


class TestDeezerPlaylistCreateFromAnother:
    def test_creates_new_playlist_and_populates_it(self) -> None:
        dz = _make_dz()
        dz.gw.create_playlist.return_value = 777
        source = MagicMock()
        source.tracks = [MagicMock()]
        matched_track = DeezerTrack(_gw_track("42"))

        with patch.object(DeezerPlaylist, "track_matcher") as mock_matcher:
            mock_matcher.return_value.match_list.return_value = [matched_track]
            result = DeezerPlaylist.create_from_another_playlist("New", source, deezer=dz)

        assert isinstance(result, DeezerPlaylist)
        assert result.playlist_id == "777"
        dz.gw.add_songs_to_playlist.assert_called_once()


# ---------------------------------------------------------------------------
# T011: track_matcher()
# ---------------------------------------------------------------------------


class TestDeezerPlaylistTrackMatcher:
    def test_track_matcher_returns_deezer_matcher_instance(self) -> None:
        from matchers.deezer_matcher import DeezerMatcher

        with patch.object(DeezerMatcher, "get_instance") as mock_get:
            mock_get.return_value = MagicMock(spec=DeezerMatcher)
            matcher = DeezerPlaylist.track_matcher()

        assert matcher is mock_get.return_value
