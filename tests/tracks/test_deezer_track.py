"""Unit tests for DeezerTrack — GW data shape, API data shape, all properties."""

from __future__ import annotations

from typing import Any

import pytest

from tracks.deezer_track import DeezerTrack

# ---------------------------------------------------------------------------
# Shared fixture data
# ---------------------------------------------------------------------------

GW_DATA: dict[str, Any] = {
    "SNG_ID": "12345",
    "SNG_TITLE": "Time",
    "ART_NAME": "Pink Floyd",
    "ALB_TITLE": "The Dark Side of the Moon",
    "DURATION": "421",
    "ISRC": "GBAYE7300007",
    "TRACK_NUMBER": "4",
}

API_DATA: dict[str, Any] = {
    "id": 12345,
    "title": "Time",
    "artist": {"name": "Pink Floyd"},
    "album": {"title": "The Dark Side of the Moon"},
    "duration": 421,
    "isrc": "GB-AYE-73-00007",
    "track_position": 4,
}


# ---------------------------------------------------------------------------
# GW data shape
# ---------------------------------------------------------------------------


class TestDeezerTrackGwShape:
    def test_track_id_from_sng_id(self) -> None:
        track = DeezerTrack(GW_DATA)
        assert track.track_id == "12345"

    def test_title_from_sng_title(self) -> None:
        track = DeezerTrack(GW_DATA)
        assert track.title == "Time"

    def test_artists_from_art_name(self) -> None:
        track = DeezerTrack(GW_DATA)
        assert track.artists == ["Pink Floyd"]

    def test_album_from_alb_title(self) -> None:
        track = DeezerTrack(GW_DATA)
        assert track.album == "The Dark Side of the Moon"

    def test_duration_from_duration_string(self) -> None:
        track = DeezerTrack(GW_DATA)
        assert track.duration == pytest.approx(421.0)

    def test_track_number_from_track_number(self) -> None:
        track = DeezerTrack(GW_DATA)
        assert track.track_number == 4

    def test_isrc_normalized_from_isrc_key(self) -> None:
        track = DeezerTrack(GW_DATA)
        assert track.isrc == "GBAYE7300007"


# ---------------------------------------------------------------------------
# API data shape
# ---------------------------------------------------------------------------


class TestDeezerTrackApiShape:
    def test_track_id_from_id(self) -> None:
        track = DeezerTrack(API_DATA)
        assert track.track_id == "12345"

    def test_title_from_title(self) -> None:
        track = DeezerTrack(API_DATA)
        assert track.title == "Time"

    def test_artists_from_artist_name(self) -> None:
        track = DeezerTrack(API_DATA)
        assert track.artists == ["Pink Floyd"]

    def test_album_from_album_title(self) -> None:
        track = DeezerTrack(API_DATA)
        assert track.album == "The Dark Side of the Moon"

    def test_duration_from_duration_int(self) -> None:
        track = DeezerTrack(API_DATA)
        assert track.duration == pytest.approx(421.0)

    def test_track_number_from_track_position(self) -> None:
        track = DeezerTrack(API_DATA)
        assert track.track_number == 4

    def test_isrc_strips_hyphens_and_normalizes(self) -> None:
        track = DeezerTrack(API_DATA)
        assert track.isrc == "GBAYE7300007"


# ---------------------------------------------------------------------------
# Permalink
# ---------------------------------------------------------------------------


class TestDeezerTrackPermalink:
    def test_permalink_canonical_form(self) -> None:
        track = DeezerTrack(GW_DATA)
        assert track.permalink == "https://www.deezer.com/track/12345"

    def test_permalink_uses_track_id_from_api(self) -> None:
        track = DeezerTrack(API_DATA)
        assert track.permalink == "https://www.deezer.com/track/12345"


# ---------------------------------------------------------------------------
# ISRC normalization
# ---------------------------------------------------------------------------


class TestDeezerTrackIsrcNormalization:
    def test_isrc_uppercase(self) -> None:
        track = DeezerTrack({**GW_DATA, "ISRC": "gbaye7300007"})
        assert track.isrc == "GBAYE7300007"

    def test_isrc_strips_hyphens(self) -> None:
        track = DeezerTrack({**GW_DATA, "ISRC": "GB-AYE-73-00007"})
        assert track.isrc == "GBAYE7300007"

    def test_isrc_none_when_absent(self) -> None:
        data = {k: v for k, v in GW_DATA.items() if k != "ISRC"}
        track = DeezerTrack(data)
        assert track.isrc is None

    def test_isrc_none_when_empty_string(self) -> None:
        track = DeezerTrack({**GW_DATA, "ISRC": ""})
        assert track.isrc is None


# ---------------------------------------------------------------------------
# track_number defaults
# ---------------------------------------------------------------------------


class TestDeezerTrackTrackNumberDefault:
    def test_track_number_defaults_to_zero_when_absent_gw(self) -> None:
        data = {k: v for k, v in GW_DATA.items() if k != "TRACK_NUMBER"}
        track = DeezerTrack(data)
        assert track.track_number == 0

    def test_track_number_defaults_to_zero_when_absent_api(self) -> None:
        data = {k: v for k, v in API_DATA.items() if k != "track_position"}
        track = DeezerTrack(data)
        assert track.track_number == 0


# ---------------------------------------------------------------------------
# Validation errors
# ---------------------------------------------------------------------------


class TestDeezerTrackValidation:
    def test_raises_on_empty_track_id(self) -> None:
        with pytest.raises(ValueError, match="non-empty numeric"):
            DeezerTrack({**GW_DATA, "SNG_ID": ""})

    def test_raises_on_non_digit_track_id(self) -> None:
        with pytest.raises(ValueError, match="non-empty numeric"):
            DeezerTrack({**GW_DATA, "SNG_ID": "abc"})

    def test_raises_when_both_id_fields_absent(self) -> None:
        data = {k: v for k, v in GW_DATA.items() if k not in ("SNG_ID", "id")}
        with pytest.raises(ValueError, match="non-empty numeric"):
            DeezerTrack(data)
