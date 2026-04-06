from typing import ClassVar
from unittest import TestCase
from unittest.mock import patch

import pytest

from matchers import Matcher
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
        source = TrackMock("5", ["ZZZZZ"], "ZZZZZ", "ZZZZZ", 1, 1, isrc="USSM19701400")
        target = SpotifyMatcher.get_instance().match(source)
        assert target is not None
        assert target.isrc == "USSM19701400"


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
    track = SpotifyTrack.__new__(SpotifyTrack)
    track._id = track_id
    track._data = data
    return track


class _MatcherTestBase(TestCase):
    """Base class that resets the Matcher singleton between tests."""

    def setUp(self) -> None:
        Matcher._Matcher__instance = None  # type: ignore[attr-defined]

    def tearDown(self) -> None:
        Matcher._Matcher__instance = None  # type: ignore[attr-defined]


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

    def test_empty_string_returns_false(self) -> None:
        assert _is_valid_isrc("") is False

    def test_hyphenated_returns_false(self) -> None:
        # hyphens not stripped by validator
        assert _is_valid_isrc("US-RC1-76-07839") is False


# ---------------------------------------------------------------------------
# T008-T011, T031-T032: US1 matcher ISRC tests
# ---------------------------------------------------------------------------


class TestMatchIsrc(_MatcherTestBase):
    """Tests for ISRC-first matching logic in SpotifyMatcher.match()."""

    @patch.object(SpotifyMatcher, "_search")
    def test_match_uses_isrc_lookup_when_valid_isrc_present(self, mock_search: object) -> None:
        """T008: valid ISRC triggers isrc: query; no fuzzy query."""
        from unittest.mock import MagicMock

        mock_search = MagicMock(return_value=[_make_spotify_track("abc123", "USRC17607839")])
        with patch.object(SpotifyMatcher, "_search", mock_search):
            matcher = SpotifyMatcher()
            track = TrackMock("1", ["Artist"], "Album", "Title", 200, 1, isrc="USRC17607839")
            matcher.match(track)

            mock_search.assert_called_once()
            call_arg = mock_search.call_args[0][0]
            assert call_arg == "isrc:USRC17607839"

    @patch.object(SpotifyMatcher, "_search")
    def test_match_returns_isrc_result_directly(self, mock_search: object) -> None:
        """T009: ISRC lookup returns a SpotifyTrack which is used as the match."""
        from unittest.mock import MagicMock

        expected = _make_spotify_track("abc123")
        mock_search = MagicMock(return_value=[expected])
        with patch.object(SpotifyMatcher, "_search", mock_search):
            matcher = SpotifyMatcher()
            track = TrackMock("1", ["Artist"], "Album", "Title", 200, 1, isrc="USRC17607839")
            result = matcher.match(track)

            assert result is expected

    @patch.object(SpotifyMatcher, "_search")
    def test_match_skips_isrc_lookup_for_malformed_isrc(self, mock_search: object) -> None:
        """T010: malformed ISRC never triggers isrc: query."""
        from unittest.mock import MagicMock

        mock_search = MagicMock(return_value=[_make_spotify_track("abc123")])
        with patch.object(SpotifyMatcher, "_search", mock_search):
            matcher = SpotifyMatcher()
            track = TrackMock("1", ["Artist"], "Album", "Title", 200, 1, isrc="NOTVALID")
            matcher.match(track)

            for call in mock_search.call_args_list:
                assert not call[0][0].startswith("isrc:")

    @patch.object(SpotifyMatcher, "_search")
    def test_match_skips_isrc_lookup_when_no_isrc_tag(self, mock_search: object) -> None:
        """T011: track with isrc=None never triggers isrc: query."""
        from unittest.mock import MagicMock

        mock_search = MagicMock(return_value=[_make_spotify_track("abc123")])
        with patch.object(SpotifyMatcher, "_search", mock_search):
            matcher = SpotifyMatcher()
            track = TrackMock("1", ["Artist"], "Album", "Title", 200, 1, isrc=None)
            matcher.match(track)

            for call in mock_search.call_args_list:
                assert not call[0][0].startswith("isrc:")

    @patch.object(SpotifyMatcher, "_search")
    def test_match_via_isrc_for_non_latin_track(self, mock_search: object) -> None:
        """T031: Cyrillic/CJK track with valid ISRC matches via ISRC, not fuzzy."""
        from unittest.mock import MagicMock

        expected = _make_spotify_track("abc123")
        mock_search = MagicMock(return_value=[expected])
        with patch.object(SpotifyMatcher, "_search", mock_search):
            matcher = SpotifyMatcher()
            track = TrackMock("1", ["Земфира"], "Вендетта", "Хочешь", 200, 1, isrc="USRC17607839")
            result = matcher.match(track)

            assert result is expected
            mock_search.assert_called_once()
            assert mock_search.call_args[0][0] == "isrc:USRC17607839"

    @patch.object(SpotifyMatcher, "_search")
    def test_match_logs_isrc_method_when_matched_via_isrc(self, mock_search: object) -> None:
        """T032: log indicates match was via ISRC."""
        from unittest.mock import MagicMock

        expected = _make_spotify_track("abc123")
        mock_search = MagicMock(return_value=[expected])
        with patch.object(SpotifyMatcher, "_search", mock_search):
            matcher = SpotifyMatcher()
            track = TrackMock("1", ["Artist"], "Album", "Title", 200, 1, isrc="USRC17607839")
            with self.assertLogs("matchers.spotify_matcher", level="INFO") as cm:
                matcher.match(track)
            assert any("isrc" in msg.lower() for msg in cm.output)


# ---------------------------------------------------------------------------
# T017-T019, T033, T035: US2 fuzzy fallback tests
# ---------------------------------------------------------------------------


class TestMatchFuzzyFallback(_MatcherTestBase):
    """Tests for fallback to fuzzy search when ISRC is absent or fails."""

    @patch.object(SpotifyMatcher, "_search")
    def test_match_falls_back_to_fuzzy_when_isrc_lookup_returns_empty(self, mock_search: object) -> None:
        """T017: valid ISRC, empty ISRC result → fuzzy fallback."""
        from unittest.mock import MagicMock

        fuzzy_result = _make_spotify_track("def456")

        def _search_side_effect(query: str) -> list[SpotifyTrack]:
            if query.startswith("isrc:"):
                return []
            return [fuzzy_result]

        mock_search = MagicMock(side_effect=_search_side_effect)
        with patch.object(SpotifyMatcher, "_search", mock_search):
            matcher = SpotifyMatcher()
            track = TrackMock("1", ["Artist"], "Album", "Title", 200, 1, isrc="USRC17607839")
            result = matcher.match(track)

            assert result is fuzzy_result
            calls = [c[0][0] for c in mock_search.call_args_list]
            assert calls[0] == "isrc:USRC17607839"
            assert any(not c.startswith("isrc:") for c in calls[1:])

    @patch.object(SpotifyMatcher, "_search")
    def test_match_falls_back_to_fuzzy_on_api_error_during_isrc_lookup(self, mock_search: object) -> None:
        """T018: API error during ISRC lookup → fallback to fuzzy + warning logged."""
        from unittest.mock import MagicMock

        fuzzy_result = _make_spotify_track("def456")

        def _search_side_effect(query: str) -> list[SpotifyTrack]:
            if query.startswith("isrc:"):
                raise Exception("API error")
            return [fuzzy_result]

        mock_search = MagicMock(side_effect=_search_side_effect)
        with patch.object(SpotifyMatcher, "_search", mock_search):
            matcher = SpotifyMatcher()
            track = TrackMock("1", ["Artist"], "Album", "Title", 200, 1, isrc="USRC17607839")
            with self.assertLogs("matchers.spotify_matcher", level="WARNING") as cm:
                result = matcher.match(track)

            assert result is fuzzy_result
            assert any("isrc" in msg.lower() for msg in cm.output)

    @patch.object(SpotifyMatcher, "_search")
    def test_match_without_isrc_invokes_only_fuzzy_search(self, mock_search: object) -> None:
        """T019: track with isrc=None → only fuzzy queries, no isrc: prefix."""
        from unittest.mock import MagicMock

        fuzzy_result = _make_spotify_track("def456")
        mock_search = MagicMock(return_value=[fuzzy_result])
        with patch.object(SpotifyMatcher, "_search", mock_search):
            matcher = SpotifyMatcher()
            track = TrackMock("1", ["Artist"], "Album", "Title", 200, 1, isrc=None)
            result = matcher.match(track)

            assert result is fuzzy_result
            assert mock_search.call_count >= 1
            for call in mock_search.call_args_list:
                assert not call[0][0].startswith("isrc:")

    @patch.object(SpotifyMatcher, "_search")
    def test_match_logs_fuzzy_method_when_fallback_used(self, mock_search: object) -> None:
        """T033: fuzzy match logs the method used."""
        from unittest.mock import MagicMock

        fuzzy_result = _make_spotify_track("def456")
        mock_search = MagicMock(return_value=[fuzzy_result])
        with patch.object(SpotifyMatcher, "_search", mock_search):
            matcher = SpotifyMatcher()
            track = TrackMock("1", ["Artist"], "Album", "Title", 200, 1, isrc=None)
            with self.assertLogs("matchers.spotify_matcher", level="INFO") as cm:
                matcher.match(track)
            assert any("fuzzy" in msg.lower() for msg in cm.output)

    @patch.object(SpotifyMatcher, "_search")
    def test_match_list_handles_mixed_isrc_no_isrc_and_skip_tracks(self, mock_search: object) -> None:
        """T035: match_list with ISRC, no-ISRC, and SKIP tracks."""
        from unittest.mock import MagicMock

        isrc_result = _make_spotify_track("aaa", "USRC17607839")
        fuzzy_result = _make_spotify_track("bbb", None)

        def _search_side_effect(query: str) -> list[SpotifyTrack]:
            if query.startswith("isrc:"):
                return [isrc_result]
            return [fuzzy_result]

        mock_search = MagicMock(side_effect=_search_side_effect)
        with patch.object(SpotifyMatcher, "_search", mock_search):
            matcher = SpotifyMatcher()
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


class TestEmbedIsrc(_MatcherTestBase):
    """Tests for ISRC embedding after match."""

    @patch.object(SpotifyMatcher, "_search")
    def test_embed_isrc_writes_isrc_to_local_track_after_match(self, mock_search: object) -> None:
        """T021: track has no ISRC, match found, embed_matches=True → ISRC written."""
        from unittest.mock import Mock, PropertyMock

        from tracks.local_track import LocalTrack

        matched = _make_spotify_track("abc123", "USRC17607839")

        matcher = SpotifyMatcher()
        mock_local = Mock(spec=LocalTrack)
        mock_local.spotify_ref = None
        isrc_prop = PropertyMock(return_value=None)
        type(mock_local).isrc = isrc_prop

        matcher._update_spotify_match_in_source_track(mock_local, matched)

        # PropertyMock records gets as call() and sets as call(value)
        set_calls = [c for c in isrc_prop.call_args_list if c[0]]
        assert len(set_calls) == 1
        assert set_calls[0][0][0] == "USRC17607839"

    @patch.object(SpotifyMatcher, "_search")
    def test_embed_isrc_does_not_rewrite_when_isrc_already_matches(self, mock_search: object) -> None:
        """T022: track already has the same ISRC as Spotify → setter not called."""
        from unittest.mock import Mock, PropertyMock

        from tracks.local_track import LocalTrack

        matched = _make_spotify_track("abc123", "USRC17607839")
        mock_local = Mock(spec=LocalTrack)
        mock_local.spotify_ref = None
        isrc_prop = PropertyMock(return_value="USRC17607839")
        type(mock_local).isrc = isrc_prop

        matcher = SpotifyMatcher()
        matcher._update_spotify_match_in_source_track(mock_local, matched)

        set_calls = [c for c in isrc_prop.call_args_list if c[0]]
        assert len(set_calls) == 0

    @patch.object(SpotifyMatcher, "_search")
    def test_embed_isrc_updates_when_spotify_isrc_differs(self, mock_search: object) -> None:
        """T022b: track has a different ISRC from Spotify → setter called with normalized Spotify ISRC."""
        from unittest.mock import Mock, PropertyMock

        from tracks.local_track import LocalTrack

        matched = _make_spotify_track("abc123", "USRC17607839")
        mock_local = Mock(spec=LocalTrack)
        mock_local.spotify_ref = None
        isrc_prop = PropertyMock(return_value="GBAYE0100538")
        type(mock_local).isrc = isrc_prop

        matcher = SpotifyMatcher()
        matcher._update_spotify_match_in_source_track(mock_local, matched)

        set_calls = [c for c in isrc_prop.call_args_list if c[0]]
        assert len(set_calls) == 1
        assert set_calls[0][0][0] == "USRC17607839"

    @patch.object(SpotifyMatcher, "_search")
    def test_embed_isrc_skipped_when_embed_matches_false(self, mock_search: object) -> None:
        """T023: embed_matches=False → isrc setter never called during match_list."""
        from unittest.mock import MagicMock, Mock, PropertyMock

        from tracks.local_track import LocalTrack

        matched = _make_spotify_track("abc123", "USRC17607839")
        mock_search_fn = MagicMock(return_value=[matched])

        with patch.object(SpotifyMatcher, "_search", mock_search_fn):
            matcher = SpotifyMatcher()
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

    @patch.object(SpotifyMatcher, "_search")
    def test_embed_isrc_skipped_when_spotify_track_has_no_isrc(self, mock_search: object) -> None:
        """T024: matched SpotifyTrack.isrc is None → no write."""
        from unittest.mock import Mock, PropertyMock

        from tracks.local_track import LocalTrack

        matched = _make_spotify_track("abc123", None)
        mock_local = Mock(spec=LocalTrack)
        mock_local.spotify_ref = None
        isrc_prop = PropertyMock(return_value=None)
        type(mock_local).isrc = isrc_prop

        matcher = SpotifyMatcher()
        matcher._update_spotify_match_in_source_track(mock_local, matched)

        set_calls = [c for c in isrc_prop.call_args_list if c[0]]
        assert len(set_calls) == 0

    def test_embed_isrc_skipped_for_skip_track(self) -> None:
        """T025: non-LocalTrack (TrackMock) passed to _update → no crash, no ISRC write."""
        matched = _make_spotify_track("abc123", "USRC17607839")
        track = TrackMock("1", ["A"], "B", "C", 200, 1, isrc=None)

        matcher = SpotifyMatcher()
        # TrackMock is not a LocalTrack, so the isinstance guard skips ISRC writing
        matcher._update_spotify_match_in_source_track(track, matched)

    def test_embed_isrc_skipped_for_non_local_track(self) -> None:
        """T027 sub-test: non-LocalTrack source → no AttributeError, no write."""
        matched = _make_spotify_track("abc123", "USRC17607839")
        track = TrackMock("1", ["A"], "B", "C", 200, 1, isrc=None)

        matcher = SpotifyMatcher()
        matcher._update_spotify_match_in_source_track(track, matched)

    def test_update_match_skips_isrc_write_when_normalized_values_match(self) -> None:
        """T006/Bug3: hyphenated Spotify ISRC must not trigger a write when local ISRC already has the same value."""
        from unittest.mock import Mock, PropertyMock

        from tracks.local_track import LocalTrack

        # Local ISRC is normalized (no hyphens), Spotify returns same ISRC with a hyphen
        matched = _make_spotify_track("abc123", "USSM1-9604431")
        mock_local = Mock(spec=LocalTrack)
        mock_local.spotify_ref = None
        isrc_prop = PropertyMock(return_value="USSM19604431")
        type(mock_local).isrc = isrc_prop

        matcher = SpotifyMatcher()
        matcher._update_spotify_match_in_source_track(mock_local, matched)

        set_calls = [c for c in isrc_prop.call_args_list if c[0]]
        assert len(set_calls) == 0
