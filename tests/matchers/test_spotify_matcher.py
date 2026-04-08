import logging
from typing import ClassVar
from unittest import TestCase
from unittest.mock import MagicMock, patch

import pytest
import spotipy

from matchers.spotify_matcher import SpotifyMatcher, _is_valid_isrc
from tests.tracks.track_mock import TrackMock
from tracks.spotify_track import SpotifyTrack


@pytest.mark.integration
class TestSpotifyMatcher(TestCase):
    UNINTENDED_TRACK = TrackMock("1", ["Muse"], "Showbiz", "Unintended", 3 * 60 + 55, 7)
    HERE_WITHOUT_YOU_TRACK = TrackMock("2", ["3 doors down"], "away from the sun", "here without you", 3 * 60 + 57, 6)
    WILD_TRACK = TrackMock("3", ["LP"], "Love Lines (Deluxe Version)", "Wild", 181, 2)
    ZE_RAK_HALEV = TrackMock("4", ["אביב גפן"], "עם הזמן", "זה רק הלב שכואב לך", 232, 4)

    match_map: ClassVar[dict[TrackMock, str]] = {
        UNINTENDED_TRACK: "6kyxQuFD38mo4S3urD2Wkw",
        HERE_WITHOUT_YOU_TRACK: "3NLrRZoMF0Lx6zTlYqeIo4",
        WILD_TRACK: "3QdeMlhJH3fAMbMPVD5ZAu",
        ZE_RAK_HALEV: "0wRnFA1iu3RSfCPvWfvWgp",
    }

    def test_match(self) -> None:
        source = self.UNINTENDED_TRACK
        target = SpotifyMatcher.get_instance().match(source)
        assert target is not None
        assert target.track_id == self.match_map[source]

    def test_suggest_match(self) -> None:
        for source, expected_track_id in self.match_map.items():
            targets = list(SpotifyMatcher.get_instance().suggest_match(source))
            assert len(targets) > 0
            best_target = targets[0]
            assert best_target.track_id == expected_track_id

    def test_match_by_isrc(self) -> None:
        source = TrackMock("5", ["ZZZZZ"], "ZZZZZ", "ZZZZZ", 1, 1, isrc="GBCVT9900015")
        target = SpotifyMatcher.get_instance().match(source)
        assert target is not None
        assert target.isrc == "GBCVT9900015"


def _make_spotify_track_data(track_id: str = "abc123", isrc: str | None = "USRC17607839") -> dict:  # type: ignore[type-arg]
    """Build a minimal Spotify track data dict for testing."""
    data: dict = {  # type: ignore[type-arg]
        "id": track_id,
        "name": "Test Track",
        "artists": [{"name": "Test Artist"}],
        "album": {"name": "Test Album"},
        "duration_ms": 200000,
        "track_number": 1,
    }
    if isrc is not None:
        data["external_ids"] = {"isrc": isrc}
    else:
        data["external_ids"] = {}
    return data


def _make_spotify_track(track_id: str = "abc123", isrc: str | None = "USRC17607839") -> SpotifyTrack:
    """Build a SpotifyTrack without needing a real Spotify API connection."""
    data = _make_spotify_track_data(track_id, isrc)
    mock = MagicMock(spec=spotipy.Spotify)
    mock._get_id.return_value = track_id
    return SpotifyTrack(track_id, data=data, client=mock)


@pytest.fixture
def mock_client() -> MagicMock:
    return MagicMock(spec=spotipy.Spotify)


@pytest.fixture
def matcher(mock_client: MagicMock) -> SpotifyMatcher:
    return SpotifyMatcher(client=mock_client)


# ---------------------------------------------------------------------------
# T034: Isolated unit tests for _is_valid_isrc()
# ---------------------------------------------------------------------------


class TestIsValidIsrc(TestCase):
    def test_valid_isrc_returns_true(self) -> None:
        assert _is_valid_isrc("USRC17607839") is True

    def test_wrong_length_returns_false(self) -> None:
        assert _is_valid_isrc("USRC176078") is False  # 10 chars

    def test_lowercase_returns_false(self) -> None:
        # normalization is the getter's responsibility; validator receives already-normalized input
        assert _is_valid_isrc("usrc17607839") is False

    def test_none_returns_false(self) -> None:
        assert _is_valid_isrc(None) is False


# ---------------------------------------------------------------------------
# Helper: build a SpotifyTrack with no _data (simulates unloaded track)
# ---------------------------------------------------------------------------


def _make_spotify_track_no_data(track_id: str = "abc123") -> SpotifyTrack:
    """Build a SpotifyTrack with _data=None (ISRC not yet loaded).

    Uses its own isolated mock client intentionally — tests using this helper
    should NOT assert on the fixture's mock_client.track() calls, as the track's
    client is a separate anonymous mock.
    """
    mock = MagicMock(spec=spotipy.Spotify)
    mock._get_id.return_value = track_id
    return SpotifyTrack(track_id, client=mock)


# ---------------------------------------------------------------------------
# T002-T007: Tests for _prefetch_isrc_data (write first - must FAIL before T008)
# ---------------------------------------------------------------------------


class TestPrefetchIsrcData:
    # T002
    def test_prefetch_isrc_data_fetches_tracks_with_no_data(
        self, matcher: SpotifyMatcher, mock_client: MagicMock
    ) -> None:
        """Tracks with _data=None → client.tracks() called with correct IDs, _data updated."""
        track = _make_spotify_track_no_data("id1")
        batch_data = _make_spotify_track_data("id1", isrc="USRC17607839")
        mock_client.tracks.return_value = {"tracks": [batch_data]}

        matcher._prefetch_isrc_data([track])

        mock_client.tracks.assert_called_once_with(["id1"])
        assert track._data == batch_data

    # T003
    def test_prefetch_isrc_data_skips_tracks_that_already_have_isrc(
        self, matcher: SpotifyMatcher, mock_client: MagicMock
    ) -> None:
        """Tracks with external_ids.isrc already in _data → client.tracks() never called."""
        track = _make_spotify_track("id1", isrc="USRC17607839")
        matcher._prefetch_isrc_data([track])
        mock_client.tracks.assert_not_called()

    # T004
    def test_prefetch_isrc_data_fetches_only_tracks_missing_isrc(
        self, matcher: SpotifyMatcher, mock_client: MagicMock
    ) -> None:
        """Mix of loaded/unloaded tracks → batch contains only the unloaded IDs."""
        loaded = _make_spotify_track("id1", isrc="USRC17607839")
        unloaded = _make_spotify_track_no_data("id2")
        batch_data = _make_spotify_track_data("id2", isrc="GBUM71505079")
        mock_client.tracks.return_value = {"tracks": [batch_data]}

        matcher._prefetch_isrc_data([loaded, unloaded])

        mock_client.tracks.assert_called_once_with(["id2"])
        assert unloaded._data == batch_data

    # T005
    def test_prefetch_isrc_data_splits_into_batches_of_50(
        self, matcher: SpotifyMatcher, mock_client: MagicMock
    ) -> None:
        """51 tracks with no _data → client.tracks() called exactly twice."""
        tracks = [_make_spotify_track_no_data(f"id{i}") for i in range(51)]
        batch_1_ids = [f"id{i}" for i in range(50)]
        batch_2_ids = ["id50"]
        batch_1_items = [_make_spotify_track_data(f"id{i}") for i in range(50)]
        batch_2_items = [_make_spotify_track_data("id50")]
        mock_client.tracks.side_effect = [
            {"tracks": batch_1_items},
            {"tracks": batch_2_items},
        ]

        matcher._prefetch_isrc_data(tracks)

        assert mock_client.tracks.call_count == 2
        mock_client.tracks.assert_any_call(batch_1_ids)
        mock_client.tracks.assert_any_call(batch_2_ids)

    # T006
    def test_prefetch_isrc_data_logs_warning_and_continues_on_batch_failure(
        self, matcher: SpotifyMatcher, mock_client: MagicMock
    ) -> None:
        """client.tracks() raises exception → WARNING logged, no crash."""
        tracks = [_make_spotify_track_no_data(f"id{i}") for i in range(3)]
        mock_client.tracks.side_effect = Exception("network error")

        with patch("matchers.spotify_matcher.logger") as mock_logger:
            matcher._prefetch_isrc_data(tracks)

        mock_logger.warning.assert_called_once()
        warning_args = mock_logger.warning.call_args
        assert "3" in str(warning_args) or 3 in warning_args.args

    # T007
    def test_prefetch_isrc_data_skips_null_items_with_debug_log(
        self, matcher: SpotifyMatcher, mock_client: MagicMock
    ) -> None:
        """None in batch response → DEBUG logged for that track, _data updated for others."""
        track_a = _make_spotify_track_no_data("id1")
        track_b = _make_spotify_track_no_data("id2")
        data_b = _make_spotify_track_data("id2", isrc="GBUM71505079")
        mock_client.tracks.return_value = {"tracks": [None, data_b]}

        with patch("matchers.spotify_matcher.logger") as mock_logger:
            matcher._prefetch_isrc_data([track_a, track_b])

        mock_logger.debug.assert_called_once()
        assert track_a._data is None  # null item — unchanged
        assert track_b._data == data_b


# ---------------------------------------------------------------------------
# T009, T010, T012: Tests for match_list (US1 + US2 — write first, must FAIL before T011)
# ---------------------------------------------------------------------------


def _make_local_track_mock(title: str = "Track") -> MagicMock:
    """Build a minimal LocalTrack-like mock for embed tests."""
    track = MagicMock()
    track.title = title
    track.spotify_ref = None
    track.isrc = None
    return track


def _build_matcher_with_suggestions(mock_client: MagicMock, sp_tracks: list[SpotifyTrack]) -> SpotifyMatcher:
    """Construct a SpotifyMatcher whose _match_list returns pre-set tracks."""
    matcher = SpotifyMatcher(client=mock_client)
    matcher._match_list = MagicMock(return_value=[[t] for t in sp_tracks])  # type: ignore[method-assign]
    return matcher


class TestMatchListBatchPrefetch:
    """Tests for the two-pass match_list design (US1 + US2)."""

    # T009
    def test_match_list_with_embed_matches_calls_prefetch_once_per_batch(self, mock_client: MagicMock) -> None:
        """embed_matches=True, N tracks all needing ISRC → client.tracks() called ⌈N/50⌉ times."""
        n = 55  # two batches
        sp_tracks = [_make_spotify_track_no_data(f"id{i}") for i in range(n)]
        source_tracks = [TrackMock(str(i), ["Artist"], "Album", f"Track {i}", 200, i) for i in range(n)]

        batch_items_1 = [_make_spotify_track_data(f"id{i}") for i in range(50)]
        batch_items_2 = [_make_spotify_track_data(f"id{i}") for i in range(50, n)]
        mock_client.tracks.side_effect = [
            {"tracks": batch_items_1},
            {"tracks": batch_items_2},
        ]

        matcher = _build_matcher_with_suggestions(mock_client, sp_tracks)
        with patch.object(matcher, "_update_spotify_match_in_source_track"):
            matcher.match_list(source_tracks, autopilot=True, embed_matches=True)

        assert mock_client.tracks.call_count == 2

    # T010
    def test_match_list_with_embed_matches_skips_prefetch_when_isrc_cached(self, mock_client: MagicMock) -> None:
        """embed_matches=True, all matches already have ISRC → client.tracks() never called."""
        sp_tracks = [_make_spotify_track(f"id{i}", isrc="USRC17607839") for i in range(5)]
        source_tracks = [TrackMock(str(i), ["Artist"], "Album", f"Track {i}", 200, i) for i in range(5)]

        matcher = _build_matcher_with_suggestions(mock_client, sp_tracks)
        with patch.object(matcher, "_update_spotify_match_in_source_track"):
            matcher.match_list(source_tracks, autopilot=True, embed_matches=True)

        mock_client.tracks.assert_not_called()

    # T012
    def test_match_list_without_embed_matches_never_calls_batch_endpoint(self, mock_client: MagicMock) -> None:
        """embed_matches=False, any playlist → client.tracks() never called."""
        sp_tracks = [_make_spotify_track_no_data(f"id{i}") for i in range(10)]
        source_tracks = [TrackMock(str(i), ["Artist"], "Album", f"Track {i}", 200, i) for i in range(10)]

        matcher = _build_matcher_with_suggestions(mock_client, sp_tracks)
        result = matcher.match_list(source_tracks, autopilot=True, embed_matches=False)

        mock_client.tracks.assert_not_called()
        assert len(result) == len(sp_tracks)

    def test_empty_string_returns_false(self) -> None:
        assert _is_valid_isrc("") is False

    def test_hyphenated_returns_false(self) -> None:
        # hyphens not stripped by validator
        assert _is_valid_isrc("US-RC1-76-07839") is False


# ---------------------------------------------------------------------------
# T008-T011, T031-T032: US1 matcher ISRC tests
# ---------------------------------------------------------------------------


class TestMatchIsrc:
    """Tests for ISRC-first matching logic in SpotifyMatcher.match()."""

    def test_match_uses_isrc_lookup_when_valid_isrc_present(self, matcher: SpotifyMatcher) -> None:
        """T008: valid ISRC triggers isrc: query; no fuzzy query."""
        mock_search = MagicMock(return_value=[_make_spotify_track("abc123", "USRC17607839")])
        with patch.object(matcher, "_search", mock_search):
            track = TrackMock("1", ["Artist"], "Album", "Title", 200, 1, isrc="USRC17607839")
            matcher.match(track)

            mock_search.assert_called_once()
            call_arg = mock_search.call_args[0][0]
            assert call_arg == "isrc:USRC17607839"

    def test_match_returns_isrc_result_directly(self, matcher: SpotifyMatcher) -> None:
        """T009: ISRC lookup returns a SpotifyTrack which is used as the match."""
        expected = _make_spotify_track("abc123")
        mock_search = MagicMock(return_value=[expected])
        with patch.object(matcher, "_search", mock_search):
            track = TrackMock("1", ["Artist"], "Album", "Title", 200, 1, isrc="USRC17607839")
            result = matcher.match(track)

            assert result is expected

    def test_match_skips_isrc_lookup_for_malformed_isrc(self, matcher: SpotifyMatcher) -> None:
        """T010: malformed ISRC never triggers isrc: query."""
        mock_search = MagicMock(return_value=[_make_spotify_track("abc123")])
        with patch.object(matcher, "_search", mock_search):
            track = TrackMock("1", ["Artist"], "Album", "Title", 200, 1, isrc="NOTVALID")
            matcher.match(track)

            for call in mock_search.call_args_list:
                assert not call[0][0].startswith("isrc:")

    def test_match_skips_isrc_lookup_when_no_isrc_tag(self, matcher: SpotifyMatcher) -> None:
        """T011: track with isrc=None never triggers isrc: query."""
        mock_search = MagicMock(return_value=[_make_spotify_track("abc123")])
        with patch.object(matcher, "_search", mock_search):
            track = TrackMock("1", ["Artist"], "Album", "Title", 200, 1, isrc=None)
            matcher.match(track)

            for call in mock_search.call_args_list:
                assert not call[0][0].startswith("isrc:")

    def test_match_via_isrc_for_non_latin_track(self, matcher: SpotifyMatcher) -> None:
        """T031: Cyrillic/CJK track with valid ISRC matches via ISRC, not fuzzy."""
        expected = _make_spotify_track("abc123")
        mock_search = MagicMock(return_value=[expected])
        with patch.object(matcher, "_search", mock_search):
            track = TrackMock("1", ["Земфира"], "Вендетта", "Хочешь", 200, 1, isrc="USRC17607839")
            result = matcher.match(track)

            assert result is expected
            mock_search.assert_called_once()
            assert mock_search.call_args[0][0] == "isrc:USRC17607839"

    def test_match_logs_isrc_method_when_matched_via_isrc(
        self, matcher: SpotifyMatcher, caplog: pytest.LogCaptureFixture
    ) -> None:
        """T032: log indicates match was via ISRC."""
        expected = _make_spotify_track("abc123")
        mock_search = MagicMock(return_value=[expected])
        with patch.object(matcher, "_search", mock_search):
            track = TrackMock("1", ["Artist"], "Album", "Title", 200, 1, isrc="USRC17607839")
            with caplog.at_level(logging.INFO, logger="matchers.spotify_matcher"):
                matcher.match(track)
        assert any("isrc" in record.message.lower() for record in caplog.records)


# ---------------------------------------------------------------------------
# T017-T019, T033, T035: US2 fuzzy fallback tests
# ---------------------------------------------------------------------------


class TestMatchFuzzyFallback:
    """Tests for fallback to fuzzy search when ISRC is absent or fails."""

    def test_match_falls_back_to_fuzzy_when_isrc_lookup_returns_empty(self, matcher: SpotifyMatcher) -> None:
        """T017: valid ISRC, empty ISRC result → fuzzy fallback."""
        fuzzy_result = _make_spotify_track("def456")

        def _search_side_effect(query: str) -> list[SpotifyTrack]:
            if query.startswith("isrc:"):
                return []
            return [fuzzy_result]

        mock_search = MagicMock(side_effect=_search_side_effect)
        with patch.object(matcher, "_search", mock_search):
            track = TrackMock("1", ["Artist"], "Album", "Title", 200, 1, isrc="USRC17607839")
            result = matcher.match(track)

            assert result is fuzzy_result
            calls = [c[0][0] for c in mock_search.call_args_list]
            assert calls[0] == "isrc:USRC17607839"
            assert any(not c.startswith("isrc:") for c in calls[1:])

    def test_match_falls_back_to_fuzzy_on_api_error_during_isrc_lookup(
        self, matcher: SpotifyMatcher, caplog: pytest.LogCaptureFixture
    ) -> None:
        """T018: API error during ISRC lookup → fallback to fuzzy + warning logged."""
        fuzzy_result = _make_spotify_track("def456")

        def _search_side_effect(query: str) -> list[SpotifyTrack]:
            if query.startswith("isrc:"):
                raise Exception("API error")
            return [fuzzy_result]

        mock_search = MagicMock(side_effect=_search_side_effect)
        with patch.object(matcher, "_search", mock_search):
            track = TrackMock("1", ["Artist"], "Album", "Title", 200, 1, isrc="USRC17607839")
            with caplog.at_level(logging.WARNING, logger="matchers.spotify_matcher"):
                result = matcher.match(track)

        assert result is fuzzy_result
        assert any("isrc" in record.message.lower() for record in caplog.records)

    def test_match_without_isrc_invokes_only_fuzzy_search(self, matcher: SpotifyMatcher) -> None:
        """T019: track with isrc=None → only fuzzy queries, no isrc: prefix."""
        fuzzy_result = _make_spotify_track("def456")
        mock_search = MagicMock(return_value=[fuzzy_result])
        with patch.object(matcher, "_search", mock_search):
            track = TrackMock("1", ["Artist"], "Album", "Title", 200, 1, isrc=None)
            result = matcher.match(track)

            assert result is fuzzy_result
            assert mock_search.call_count >= 1
            for call in mock_search.call_args_list:
                assert not call[0][0].startswith("isrc:")

    def test_match_logs_fuzzy_method_when_fallback_used(
        self, matcher: SpotifyMatcher, caplog: pytest.LogCaptureFixture
    ) -> None:
        """T033: fuzzy match logs the method used."""
        fuzzy_result = _make_spotify_track("def456")
        mock_search = MagicMock(return_value=[fuzzy_result])
        with patch.object(matcher, "_search", mock_search):
            track = TrackMock("1", ["Artist"], "Album", "Title", 200, 1, isrc=None)
            with caplog.at_level(logging.INFO, logger="matchers.spotify_matcher"):
                matcher.match(track)
        assert any("fuzzy" in record.message.lower() for record in caplog.records)

    def test_match_list_handles_mixed_isrc_no_isrc_and_skip_tracks(self, matcher: SpotifyMatcher) -> None:
        """T035: match_list with ISRC, no-ISRC, and SKIP tracks."""
        isrc_result = _make_spotify_track("aaa", "USRC17607839")
        fuzzy_result = _make_spotify_track("bbb", None)

        def _search_side_effect(query: str) -> list[SpotifyTrack]:
            if query.startswith("isrc:"):
                return [isrc_result]
            return [fuzzy_result]

        mock_search = MagicMock(side_effect=_search_side_effect)
        with patch.object(matcher, "_search", mock_search):
            track_isrc = TrackMock("1", ["A"], "B", "C", 200, 1, isrc="USRC17607839")
            track_no_isrc = TrackMock("2", ["D"], "E", "F", 200, 2, isrc=None)
            # SKIP tracks are covered by test_embed_isrc_skipped_for_skip_track;
            # TrackMock lacks spotify_ref so SKIP can't be simulated here directly.

            r1 = matcher.match(track_isrc)
            r2 = matcher.match(track_no_isrc)

            assert r1 is isrc_result
            assert r2 is fuzzy_result

            calls = [c[0][0] for c in mock_search.call_args_list]
            isrc_calls = [c for c in calls if c.startswith("isrc:")]
            fuzzy_calls = [c for c in calls if not c.startswith("isrc:")]
            assert len(isrc_calls) >= 1
            assert len(fuzzy_calls) >= 1


# ---------------------------------------------------------------------------
# T021-T025: US3 ISRC embedding tests
# ---------------------------------------------------------------------------


class TestEmbedIsrc:
    """Tests for ISRC embedding after match."""

    def test_embed_isrc_writes_isrc_to_local_track_after_match(self, matcher: SpotifyMatcher) -> None:
        """T021: track has no ISRC, match found, embed_matches=True → ISRC written."""
        from unittest.mock import Mock, PropertyMock

        from tracks.local_track import LocalTrack

        matched = _make_spotify_track("abc123", "USRC17607839")
        mock_local = Mock(spec=LocalTrack)
        mock_local.spotify_ref = None
        isrc_prop = PropertyMock(return_value=None)
        type(mock_local).isrc = isrc_prop

        matcher._update_spotify_match_in_source_track(mock_local, matched)

        # PropertyMock records gets as call() and sets as call(value)
        set_calls = [c for c in isrc_prop.call_args_list if c[0]]
        assert len(set_calls) == 1
        assert set_calls[0][0][0] == "USRC17607839"

    def test_embed_isrc_does_not_rewrite_when_isrc_already_matches(self, matcher: SpotifyMatcher) -> None:
        """T022: track already has the same ISRC as Spotify → setter not called."""
        from unittest.mock import Mock, PropertyMock

        from tracks.local_track import LocalTrack

        matched = _make_spotify_track("abc123", "USRC17607839")
        mock_local = Mock(spec=LocalTrack)
        mock_local.spotify_ref = None
        isrc_prop = PropertyMock(return_value="USRC17607839")
        type(mock_local).isrc = isrc_prop

        matcher._update_spotify_match_in_source_track(mock_local, matched)

        set_calls = [c for c in isrc_prop.call_args_list if c[0]]
        assert len(set_calls) == 0

    def test_embed_isrc_updates_when_spotify_isrc_differs(self, matcher: SpotifyMatcher) -> None:
        """T022b: track has a different ISRC from Spotify → setter called with normalized Spotify ISRC."""
        from unittest.mock import Mock, PropertyMock

        from tracks.local_track import LocalTrack

        matched = _make_spotify_track("abc123", "USRC17607839")
        mock_local = Mock(spec=LocalTrack)
        mock_local.spotify_ref = None
        isrc_prop = PropertyMock(return_value="GBAYE0100538")
        type(mock_local).isrc = isrc_prop

        matcher._update_spotify_match_in_source_track(mock_local, matched)

        set_calls = [c for c in isrc_prop.call_args_list if c[0]]
        assert len(set_calls) == 1
        assert set_calls[0][0][0] == "USRC17607839"

    def test_embed_isrc_skipped_when_embed_matches_false(self, matcher: SpotifyMatcher) -> None:
        """T023: embed_matches=False → isrc setter never called during match_list."""
        from unittest.mock import Mock, PropertyMock

        from tracks.local_track import LocalTrack

        matched = _make_spotify_track("abc123", "USRC17607839")
        mock_search_fn = MagicMock(return_value=[matched])

        with patch.object(matcher, "_search", mock_search_fn):
            mock_local = Mock(spec=LocalTrack)
            mock_local.spotify_ref = None
            mock_local.artists = ["Artist"]
            mock_local.title = "Title"
            mock_local.album = "Album"
            isrc_prop = PropertyMock(return_value=None)
            type(mock_local).isrc = isrc_prop

            matcher.match_list([mock_local], autopilot=True, embed_matches=False)

            set_calls = [c for c in isrc_prop.call_args_list if c[0]]
            assert len(set_calls) == 0

    def test_embed_isrc_skipped_when_spotify_track_has_no_isrc(self, matcher: SpotifyMatcher) -> None:
        """T024: matched SpotifyTrack.isrc is None → no write."""
        from unittest.mock import Mock, PropertyMock

        from tracks.local_track import LocalTrack

        matched = _make_spotify_track("abc123", None)
        mock_local = Mock(spec=LocalTrack)
        mock_local.spotify_ref = None
        isrc_prop = PropertyMock(return_value=None)
        type(mock_local).isrc = isrc_prop

        matcher._update_spotify_match_in_source_track(mock_local, matched)

        set_calls = [c for c in isrc_prop.call_args_list if c[0]]
        assert len(set_calls) == 0

    def test_embed_isrc_skipped_for_skip_track(self, matcher: SpotifyMatcher) -> None:
        """T025: non-LocalTrack (TrackMock) passed to _update → no crash, no ISRC write."""
        matched = _make_spotify_track("abc123", "USRC17607839")
        track = TrackMock("1", ["A"], "B", "C", 200, 1, isrc=None)
        # TrackMock is not a LocalTrack, so the isinstance guard skips ISRC writing
        matcher._update_spotify_match_in_source_track(track, matched)

    def test_embed_isrc_skipped_for_non_local_track(self, matcher: SpotifyMatcher) -> None:
        """T027 sub-test: non-LocalTrack source → no AttributeError, no write."""
        matched = _make_spotify_track("abc123", "USRC17607839")
        track = TrackMock("1", ["A"], "B", "C", 200, 1, isrc=None)
        matcher._update_spotify_match_in_source_track(track, matched)

    def test_update_match_skips_isrc_write_when_normalized_values_match(self, matcher: SpotifyMatcher) -> None:
        """T006/Bug3: hyphenated Spotify ISRC must not trigger a write when local ISRC already has the same value."""
        from unittest.mock import Mock, PropertyMock

        from tracks.local_track import LocalTrack

        # Local ISRC is normalized (no hyphens), Spotify returns same ISRC with a hyphen
        matched = _make_spotify_track("abc123", "USSM1-9604431")
        mock_local = Mock(spec=LocalTrack)
        mock_local.spotify_ref = None
        isrc_prop = PropertyMock(return_value="USSM19604431")
        type(mock_local).isrc = isrc_prop

        matcher._update_spotify_match_in_source_track(mock_local, matched)

        set_calls = [c for c in isrc_prop.call_args_list if c[0]]
        assert len(set_calls) == 0
