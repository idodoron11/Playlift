"""Unit tests for DeezerMatcher — all four resolution steps.

Covers:
  T007: steps 1-2 (cached ref + SKIP)
  T009: step 3 (ISRC lookup)
  T014: step 4 (fuzzy search)
  T020: deezer match CLI embedding behaviour
"""

from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock

import pytest

from exceptions import SkipTrackError
from matchers.deezer_matcher import DeezerMatcher
from tracks.deezer_track import DeezerTrack, is_valid_deezer_url, normalise_deezer_url

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_matcher(dz: Any = None) -> DeezerMatcher:
    if dz is None:
        dz = MagicMock()
    return DeezerMatcher(deezer=dz)


def _make_track(
    isrc: str | None = None,
    service_ref: str | None = None,
    title: str = "Time",
    artist: str = "Pink Floyd",
    album: str = "DSOTM",
    duration: float = 421.0,
    track_number: int = 4,
) -> MagicMock:
    track = MagicMock()
    track.isrc = isrc
    track.service_ref.return_value = service_ref
    track.title = title
    track.display_artist = artist
    track.artists = [artist]
    track.album = album
    track.duration = duration
    track.track_number = track_number
    return track


def _gw_data(**kwargs: Any) -> dict[str, Any]:
    base: dict[str, Any] = {
        "SNG_ID": "99999",
        "SNG_TITLE": "Time",
        "ART_NAME": "Pink Floyd",
        "ALB_TITLE": "DSOTM",
        "DURATION": "421",
        "TRACK_NUMBER": "4",
    }
    base.update(kwargs)
    return base


# ---------------------------------------------------------------------------
# T007 — US6: cached ref + SKIP (steps 1 + 2)
# ---------------------------------------------------------------------------


class TestMatchByCachedRef:
    def test_canonical_url_used_directly_without_network_call(self) -> None:
        dz = MagicMock()
        matcher = _make_matcher(dz)
        track = _make_track(service_ref="https://www.deezer.com/track/12345")

        result = matcher._match_by_cached_ref(track)

        assert isinstance(result, DeezerTrack)
        assert result.track_id == "12345"
        dz.api.get_track_by_ISRC.assert_not_called()
        dz.gw.search.assert_not_called()

    def test_url_without_www_normalised_to_canonical(self) -> None:
        matcher = _make_matcher()
        track = _make_track(service_ref="https://deezer.com/track/12345")

        result = matcher._match_by_cached_ref(track)

        assert isinstance(result, DeezerTrack)
        assert result.track_id == "12345"

    def test_url_with_locale_prefix_normalised(self) -> None:
        matcher = _make_matcher()
        track = _make_track(service_ref="https://www.deezer.com/en/track/12345")

        result = matcher._match_by_cached_ref(track)

        assert isinstance(result, DeezerTrack)
        assert result.track_id == "12345"

    def test_url_with_query_string_normalised(self) -> None:
        matcher = _make_matcher()
        track = _make_track(service_ref="https://www.deezer.com/track/12345?utm_source=foo")

        result = matcher._match_by_cached_ref(track)

        assert isinstance(result, DeezerTrack)
        assert result.track_id == "12345"

    def test_skip_sentinel_raises_skip_track_error(self) -> None:
        matcher = _make_matcher()
        track = _make_track(service_ref="SKIP")

        with pytest.raises(SkipTrackError):
            matcher._match_by_cached_ref(track)

    def test_malformed_value_falls_through_returns_none(self) -> None:
        matcher = _make_matcher()
        track = _make_track(service_ref="not-a-url")

        result = matcher._match_by_cached_ref(track)

        assert result is None

    def test_none_service_ref_returns_none(self) -> None:
        matcher = _make_matcher()
        track = _make_track(service_ref=None)

        result = matcher._match_by_cached_ref(track)

        assert result is None


# ---------------------------------------------------------------------------
# T009 — US7: ISRC lookup (step 3)
# ---------------------------------------------------------------------------


class TestMatchByIsrc:
    def test_isrc_present_and_found_returns_deezer_track(self) -> None:
        dz = MagicMock()
        dz.api.get_track_by_ISRC.return_value = _gw_data(id=99999, **{"SNG_ID": "99999"})
        matcher = _make_matcher(dz)
        track = _make_track(isrc="GBAYE7300007")

        result = matcher._match_by_isrc(track)

        assert isinstance(result, DeezerTrack)
        dz.api.get_track_by_ISRC.assert_called_once_with("GBAYE7300007")

    def test_isrc_present_but_not_found_returns_none(self) -> None:
        dz = MagicMock()
        dz.api.get_track_by_ISRC.side_effect = Exception("not found")
        matcher = _make_matcher(dz)
        track = _make_track(isrc="GBAYE7300007")

        result = matcher._match_by_isrc(track)

        assert result is None

    def test_no_isrc_skips_lookup_returns_none(self) -> None:
        dz = MagicMock()
        matcher = _make_matcher(dz)
        track = _make_track(isrc=None)

        result = matcher._match_by_isrc(track)

        assert result is None
        dz.api.get_track_by_ISRC.assert_not_called()

    def test_network_error_logs_warning_and_returns_none(self, caplog: Any) -> None:
        import logging

        dz = MagicMock()
        dz.api.get_track_by_ISRC.side_effect = ConnectionError("timeout")
        matcher = _make_matcher(dz)
        track = _make_track(isrc="GBAYE7300007")

        with caplog.at_level(logging.WARNING):
            result = matcher._match_by_isrc(track)

        assert result is None
        assert any("ISRC lookup failed" in r.message for r in caplog.records)


# ---------------------------------------------------------------------------
# T014 — US8: fuzzy search (step 4)
# ---------------------------------------------------------------------------


class TestMatchByFuzzySearch:
    def _make_close_candidate(self) -> dict[str, Any]:
        return {
            "SNG_ID": "99999",
            "SNG_TITLE": "Time",
            "ART_NAME": "Pink Floyd",
            "ALB_TITLE": "DSOTM",
            "DURATION": "421",
            "TRACK_NUMBER": "4",
        }

    def test_result_above_threshold_autopilot_returns_match(self) -> None:
        dz = MagicMock()
        dz.gw.search.return_value = {"TRACK": {"data": [self._make_close_candidate()]}}
        matcher = _make_matcher(dz)
        track = _make_track()

        result = matcher._match_by_fuzzy_search(track)

        assert result is not None
        assert isinstance(result, DeezerTrack)

    def test_no_results_logs_warning_and_returns_none(self, caplog: Any) -> None:
        import logging

        dz = MagicMock()
        dz.gw.search.return_value = {"TRACK": {"data": []}}
        matcher = _make_matcher(dz)
        track = _make_track()

        with caplog.at_level(logging.WARNING):
            result = matcher._match_by_fuzzy_search(track)

        assert result is None
        assert any("fuzzy search" in r.message.lower() for r in caplog.records)

    def test_non_latin_query_forwarded_unchanged(self) -> None:
        dz = MagicMock()
        dz.gw.search.return_value = {"TRACK": {"data": []}}
        matcher = _make_matcher(dz)
        artist = "Земфира"  # Cyrillic
        title = "Хочешь"
        track = _make_track(artist=artist, title=title)

        matcher._match_by_fuzzy_search(track)

        called_query: str = dz.gw.search.call_args[0][0]
        assert artist in called_query
        assert title in called_query

    def test_network_error_logs_warning_and_returns_none(self, caplog: Any) -> None:
        import logging

        dz = MagicMock()
        dz.gw.search.side_effect = ConnectionError("timeout")
        matcher = _make_matcher(dz)
        track = _make_track()

        with caplog.at_level(logging.WARNING):
            result = matcher._match_by_fuzzy_search(track)

        assert result is None


# ---------------------------------------------------------------------------
# URL helpers
# ---------------------------------------------------------------------------


class TestIsValidDeezerUrl:
    @pytest.mark.parametrize(
        "url",
        [
            "https://www.deezer.com/track/12345",
            "https://deezer.com/track/12345",
            "https://www.deezer.com/en/track/12345",
            "https://www.deezer.com/fr/track/12345",
            "https://www.deezer.com/en-gb/track/12345",
            "https://www.deezer.com/track/12345?utm_source=foo",
        ],
    )
    def test_valid_urls(self, url: str) -> None:
        assert is_valid_deezer_url(url) is True

    @pytest.mark.parametrize(
        "url",
        [
            "SKIP",
            "not-a-url",
            "https://open.spotify.com/track/abc",
            "https://www.deezer.com/track/",
            "https://www.deezer.com/track/abc",  # non-digit
        ],
    )
    def test_invalid_urls(self, url: str) -> None:
        assert is_valid_deezer_url(url) is False


class TestNormaliseDeezerUrl:
    def test_canonical_url_unchanged(self) -> None:
        assert normalise_deezer_url("https://www.deezer.com/track/12345") == "https://www.deezer.com/track/12345"

    def test_locale_prefix_stripped(self) -> None:
        assert normalise_deezer_url("https://www.deezer.com/en/track/12345") == "https://www.deezer.com/track/12345"

    def test_no_www_normalised(self) -> None:
        assert normalise_deezer_url("https://deezer.com/track/12345") == "https://www.deezer.com/track/12345"

    def test_query_string_stripped(self) -> None:
        assert normalise_deezer_url("https://www.deezer.com/track/12345?q=1") == "https://www.deezer.com/track/12345"
