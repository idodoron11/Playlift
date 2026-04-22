"""Tests for LocalTrack.isrc getter and setter (T012, T026)."""

import contextlib
from typing import Any
from unittest import TestCase
from unittest.mock import MagicMock, Mock, PropertyMock, patch

from tracks.local_track import LocalTrack, _normalize_isrc


class TestNormalizeIsrc(TestCase):
    """Unit tests for the _normalize_isrc helper."""

    def test_uppercase_passthrough(self) -> None:
        assert _normalize_isrc("USRC17607839") == "USRC17607839"

    def test_lowercase_normalized(self) -> None:
        assert _normalize_isrc("usrc17607839") == "USRC17607839"

    def test_mixed_case_normalized(self) -> None:
        assert _normalize_isrc("UsRc17607839") == "USRC17607839"

    def test_hyphens_stripped(self) -> None:
        assert _normalize_isrc("US-RC1-76-07839") == "USRC17607839"

    def test_hyphens_and_lowercase(self) -> None:
        assert _normalize_isrc("us-rc1-76-07839") == "USRC17607839"


class _LocalTrackTestBase(TestCase):
    """Base that creates a LocalTrack with mocked file I/O."""

    def _make_local_track(self, mutagen_file: Any, audio_file: Any = None) -> LocalTrack:
        """Create a LocalTrack without touching the filesystem."""
        with patch.object(LocalTrack, "reload_metadata"):
            track = LocalTrack.__new__(LocalTrack)
            track._file_path = "/fake/track.mp3"
            track._mutagen_file = mutagen_file
            track._audio = audio_file or MagicMock()
        return track

    @staticmethod
    def _isrc_setter_patch() -> contextlib.AbstractContextManager[Any]:
        """Patch LocalTrack.isrc so the getter returns None but the real setter runs."""
        original_fset = LocalTrack.isrc.fset  # type: ignore[attr-defined]
        return patch.object(
            LocalTrack,
            "isrc",
            new_callable=lambda: property(fget=lambda self: None, fset=original_fset),
        )


# ---------------------------------------------------------------------------
# T012: LocalTrack.isrc getter tests
# ---------------------------------------------------------------------------


class TestLocalTrackIsrcGetterMp3(_LocalTrackTestBase):
    """ISRC getter for MP3 files (TSRC frame)."""

    def test_isrc_returns_value_from_tsrc_frame(self) -> None:
        from mutagen.mp3 import MP3

        mock_mp3 = MagicMock(spec=MP3)
        mock_frame = MagicMock()
        mock_frame.text = ["USRC17607839"]
        mock_mp3.tags = {"TSRC": mock_frame}
        mock_mp3.__class__ = MP3

        track = self._make_local_track(mock_mp3)
        assert track.isrc == "USRC17607839"

    def test_isrc_normalizes_lowercase(self) -> None:
        from mutagen.mp3 import MP3

        mock_mp3 = MagicMock(spec=MP3)
        mock_frame = MagicMock()
        mock_frame.text = ["usrc17607839"]
        mock_mp3.tags = {"TSRC": mock_frame}
        mock_mp3.__class__ = MP3

        track = self._make_local_track(mock_mp3)
        assert track.isrc == "USRC17607839"

    def test_isrc_strips_hyphens(self) -> None:
        from mutagen.mp3 import MP3

        mock_mp3 = MagicMock(spec=MP3)
        mock_frame = MagicMock()
        mock_frame.text = ["US-RC1-76-07839"]
        mock_mp3.tags = {"TSRC": mock_frame}
        mock_mp3.__class__ = MP3

        track = self._make_local_track(mock_mp3)
        assert track.isrc == "USRC17607839"

    def test_isrc_returns_none_when_no_tsrc_frame(self) -> None:
        from mutagen.mp3 import MP3

        mock_mp3 = MagicMock(spec=MP3)
        mock_mp3.tags = {}
        mock_mp3.__class__ = MP3

        track = self._make_local_track(mock_mp3)
        assert track.isrc is None

    def test_isrc_returns_none_when_tags_is_none(self) -> None:
        from mutagen.mp3 import MP3

        mock_mp3 = MagicMock(spec=MP3)
        mock_mp3.tags = None
        mock_mp3.__class__ = MP3

        track = self._make_local_track(mock_mp3)
        assert track.isrc is None


class TestLocalTrackIsrcGetterFlac(_LocalTrackTestBase):
    """ISRC getter for FLAC files (Vorbis isrc comment)."""

    def test_isrc_returns_value_from_vorbis_comment(self) -> None:
        from mutagen.flac import FLAC

        mock_flac = MagicMock(spec=FLAC)
        mock_flac.__class__ = FLAC

        mock_audio = MagicMock()
        mock_tag = MagicMock()
        mock_tag.first = "USRC17607839"
        mock_audio.__getitem__ = Mock(return_value=mock_tag)

        track = self._make_local_track(mock_flac, audio_file=mock_audio)
        assert track.isrc == "USRC17607839"

    def test_isrc_returns_none_when_tag_absent(self) -> None:
        from mutagen.flac import FLAC

        mock_flac = MagicMock(spec=FLAC)
        mock_flac.__class__ = FLAC

        mock_audio = MagicMock()
        mock_audio.__getitem__ = Mock(return_value=None)

        track = self._make_local_track(mock_flac, audio_file=mock_audio)
        assert track.isrc is None


class TestLocalTrackIsrcGetterM4a(_LocalTrackTestBase):
    """ISRC getter for M4A files (iTunes freeform tag via _get_custom_tag)."""

    def test_isrc_returns_value_from_itunes_freeform_tag(self) -> None:
        from mutagen.mp4 import MP4

        mock_mp4 = MagicMock(spec=MP4)
        mock_mp4.__class__ = MP4  # type: ignore[assignment]
        tags_dict = {"----:com.apple.iTunes:ISRC": [b"USRC17607839"]}
        mock_mp4.tags = tags_dict
        # _get_custom_tag accesses self._mutagen_file[tag_name] directly
        mock_mp4.__getitem__ = Mock(side_effect=lambda key: tags_dict[key])
        mock_mp4.__contains__ = Mock(side_effect=lambda key: key in tags_dict)

        track = self._make_local_track(mock_mp4)
        assert track.isrc == "USRC17607839"

    def test_isrc_returns_none_when_tag_absent(self) -> None:
        from mutagen.mp4 import MP4

        mock_mp4 = MagicMock(spec=MP4)
        mock_mp4.__class__ = MP4  # type: ignore[assignment]
        tags_dict: dict = {}  # type: ignore[type-arg]
        mock_mp4.tags = tags_dict

        track = self._make_local_track(mock_mp4)
        assert track.isrc is None

    def test_isrc_returns_value_from_lowercase_itunes_key(self) -> None:
        from mutagen.mp4 import MP4, MP4FreeForm

        mock_mp4 = MagicMock(spec=MP4)
        mock_mp4.__class__ = MP4  # type: ignore[assignment]
        # Key is lowercase, as written by Apple Music / some encoders
        tags_dict = {"----:com.apple.iTunes:isrc": [MP4FreeForm(b"USSM19604431")]}  # type: ignore[no-untyped-call]
        mock_mp4.tags = tags_dict
        mock_mp4.__getitem__ = Mock(side_effect=lambda key: tags_dict[key])
        mock_mp4.__contains__ = Mock(side_effect=lambda key: key in tags_dict)

        track = self._make_local_track(mock_mp4)
        assert track.isrc == "USSM19604431"  # Must not return None


# ---------------------------------------------------------------------------
# T026: LocalTrack.isrc setter tests
# ---------------------------------------------------------------------------


class TestLocalTrackIsrcSetterMp3(_LocalTrackTestBase):
    """ISRC setter for MP3 files (TSRC frame)."""

    def test_isrc_setter_writes_tsrc_frame(self) -> None:
        from mutagen.mp3 import MP3

        mock_mp3 = MagicMock(spec=MP3)
        mock_mp3.__class__ = MP3
        mock_mp3.tags = MagicMock()
        mock_mp3.tags.__contains__ = Mock(return_value=False)

        track = self._make_local_track(mock_mp3)
        with self._isrc_setter_patch():
            track.isrc = "USRC17607839"

        mock_mp3.tags.add.assert_called_once()
        mock_mp3.save.assert_called_once()

    def test_isrc_setter_does_not_overwrite_existing(self) -> None:
        from mutagen.mp3 import MP3

        mock_mp3 = MagicMock(spec=MP3)
        mock_mp3.__class__ = MP3
        mock_frame = MagicMock()
        mock_frame.text = ["GBAYE0100538"]
        mock_mp3.tags = {"TSRC": mock_frame}

        track = self._make_local_track(mock_mp3)
        track.isrc = "USRC17607839"

        mock_mp3.save.assert_not_called()

    def test_isrc_setter_logs_warning_on_save_failure(self) -> None:
        from mutagen.mp3 import MP3

        mock_mp3 = MagicMock(spec=MP3)
        mock_mp3.__class__ = MP3
        mock_mp3.tags = MagicMock()
        mock_mp3.tags.__contains__ = Mock(return_value=False)
        mock_mp3.save.side_effect = OSError("disk full")

        track = self._make_local_track(mock_mp3)
        with self._isrc_setter_patch(), self.assertLogs("tracks.local_track", level="WARNING") as cm:
            track.isrc = "USRC17607839"

        assert any("ISRC" in msg or "isrc" in msg.lower() for msg in cm.output)


class TestLocalTrackIsrcSetterFlac(_LocalTrackTestBase):
    """ISRC setter for FLAC files."""

    def test_isrc_setter_writes_vorbis_comment(self) -> None:
        from mutagen.flac import FLAC

        mock_flac = MagicMock(spec=FLAC)
        mock_flac.__class__ = FLAC
        mock_flac.tags = MagicMock()

        track = self._make_local_track(mock_flac)
        with self._isrc_setter_patch():
            track.isrc = "USRC17607839"

        mock_flac.tags.__setitem__.assert_called_once_with("isrc", "USRC17607839")
        mock_flac.save.assert_called_once()


class TestLocalTrackIsrcSetterM4a(_LocalTrackTestBase):
    """ISRC setter for M4A files (via _set_custom_tag)."""

    def test_isrc_setter_writes_itunes_freeform_tag(self) -> None:
        from mutagen.mp4 import MP4

        mock_mp4 = MagicMock(spec=MP4)
        mock_mp4.__class__ = MP4  # type: ignore[assignment]
        mock_mp4.tags = MagicMock()
        mock_mp4.tags.__contains__ = Mock(return_value=False)

        mock_audio = MagicMock()

        track = self._make_local_track(mock_mp4, audio_file=mock_audio)
        with self._isrc_setter_patch():
            track.isrc = "USRC17607839"

        # _set_custom_tag for MP4 must write a proper MP4FreeForm list, not raw bytes
        from mutagen.mp4 import MP4FreeForm

        call_args = mock_mp4.tags.__setitem__.call_args
        assert call_args is not None
        key, value = call_args.args
        assert key == "----:com.apple.iTunes:ISRC"
        assert isinstance(value, list)
        assert all(isinstance(v, MP4FreeForm) for v in value)

    def test_isrc_setter_skips_write_when_lowercase_key_exists(self) -> None:
        from mutagen.mp4 import MP4, MP4FreeForm

        mock_mp4 = MagicMock(spec=MP4)
        mock_mp4.__class__ = MP4  # type: ignore[assignment]
        tags_dict = {"----:com.apple.iTunes:isrc": [MP4FreeForm(b"USSM19604431")]}  # type: ignore[no-untyped-call]
        mock_mp4.tags = tags_dict
        mock_mp4.__getitem__ = Mock(side_effect=lambda key: tags_dict[key])
        mock_mp4.__contains__ = Mock(side_effect=lambda key: key in tags_dict)

        track = self._make_local_track(mock_mp4)
        track.isrc = "USSM19604431"  # Must not write a new atom
        mock_mp4.save.assert_not_called()

    def test_isrc_setter_writes_mp4freeform_not_raw_bytes(self) -> None:
        from mutagen.mp4 import MP4, MP4FreeForm

        mock_mp4 = MagicMock(spec=MP4)
        mock_mp4.__class__ = MP4  # type: ignore[assignment]
        written: dict = {}  # type: ignore[type-arg]
        mock_mp4.tags = MagicMock()
        mock_mp4.tags.__contains__ = Mock(return_value=False)
        mock_mp4.tags.__setitem__ = Mock(side_effect=lambda k, v: written.update({k: v}))

        mock_audio = MagicMock()

        track = self._make_local_track(mock_mp4, audio_file=mock_audio)
        with self._isrc_setter_patch():
            track.isrc = "USSM19604431"

        value = written.get("----:com.apple.iTunes:ISRC")
        assert isinstance(value, list)
        assert all(isinstance(v, MP4FreeForm) for v in value)


# ---------------------------------------------------------------------------
# T003: TestLocalTrackEmbedMatch — write first, must FAIL before T004
# ---------------------------------------------------------------------------


class TestLocalTrackEmbedMatch(_LocalTrackTestBase):
    """Tests for LocalTrack.embed_match — persists service ref and ISRC."""

    def _make_service_track_mock(
        self,
        service_name: str = "SPOTIFY",
        permalink: str = "https://open.spotify.com/track/abc123",
        isrc: str | None = "USRC17607839",
    ) -> Any:
        from tracks import ServiceTrack

        mock_match = Mock(spec=ServiceTrack)
        mock_match.service_name = service_name
        mock_match.permalink = permalink
        mock_match.isrc = isrc
        return mock_match

    def test_embed_match_writes_service_ref_when_unset(self) -> None:
        track = self._make_local_track(MagicMock())
        match = self._make_service_track_mock(isrc=None)

        with (
            patch.object(LocalTrack, "service_ref", return_value=None),
            patch.object(track, "_set_custom_tag") as mock_set,
        ):
            track.embed_match(match)

        mock_set.assert_called_once_with("SPOTIFY", "https://open.spotify.com/track/abc123")

    def test_embed_match_skips_service_ref_when_already_matches(self) -> None:
        track = self._make_local_track(MagicMock())
        permalink = "https://open.spotify.com/track/abc123"
        match = self._make_service_track_mock(permalink=permalink, isrc=None)

        with (
            patch.object(LocalTrack, "service_ref", return_value=permalink),
            patch.object(track, "_set_custom_tag") as mock_set,
        ):
            track.embed_match(match)

        mock_set.assert_not_called()

    def test_embed_match_updates_service_ref_when_differs(self) -> None:
        track = self._make_local_track(MagicMock())
        new_permalink = "https://open.spotify.com/track/newid"
        match = self._make_service_track_mock(permalink=new_permalink, isrc=None)

        with (
            patch.object(LocalTrack, "service_ref", return_value="https://open.spotify.com/track/oldid"),
            patch.object(track, "_set_custom_tag") as mock_set,
        ):
            track.embed_match(match)

        mock_set.assert_called_once_with("SPOTIFY", new_permalink)

    def test_embed_match_does_not_touch_other_service_ref(self) -> None:
        track = self._make_local_track(MagicMock())
        match = self._make_service_track_mock(service_name="SPOTIFY", isrc=None)

        with (
            patch.object(LocalTrack, "service_ref", return_value=None),
            patch.object(track, "_set_custom_tag") as mock_set,
        ):
            track.embed_match(match)

        for call in mock_set.call_args_list:
            assert call.args[0] == "SPOTIFY"

    def test_embed_match_writes_isrc_when_missing(self) -> None:
        track = self._make_local_track(MagicMock())
        match = self._make_service_track_mock(isrc="USRC17607839")
        isrc_prop = PropertyMock(return_value=None)

        with (
            patch.object(LocalTrack, "service_ref", return_value=match.permalink),
            patch.object(LocalTrack, "isrc", isrc_prop),
        ):
            track.embed_match(match)

        set_calls = [c for c in isrc_prop.call_args_list if c.args]
        assert len(set_calls) == 1
        assert set_calls[0].args[0] == "USRC17607839"

    def test_embed_match_skips_isrc_when_already_matches(self) -> None:
        track = self._make_local_track(MagicMock())
        match = self._make_service_track_mock(isrc="USRC17607839")
        isrc_prop = PropertyMock(return_value="USRC17607839")

        with (
            patch.object(LocalTrack, "service_ref", return_value=match.permalink),
            patch.object(LocalTrack, "isrc", isrc_prop),
        ):
            track.embed_match(match)

        set_calls = [c for c in isrc_prop.call_args_list if c.args]
        assert len(set_calls) == 0

    def test_embed_match_updates_isrc_when_differs(self) -> None:
        track = self._make_local_track(MagicMock())
        match = self._make_service_track_mock(isrc="USRC17607839")
        isrc_prop = PropertyMock(return_value="GBAYE0100538")

        with (
            patch.object(LocalTrack, "service_ref", return_value=match.permalink),
            patch.object(LocalTrack, "isrc", isrc_prop),
        ):
            track.embed_match(match)

        set_calls = [c for c in isrc_prop.call_args_list if c.args]
        assert len(set_calls) == 1
        assert set_calls[0].args[0] == "USRC17607839"

    def test_embed_match_skips_isrc_when_match_has_no_isrc(self) -> None:
        track = self._make_local_track(MagicMock())
        match = self._make_service_track_mock(isrc=None)
        isrc_prop = PropertyMock(return_value=None)

        with (
            patch.object(LocalTrack, "service_ref", return_value=None),
            patch.object(track, "_set_custom_tag"),
            patch.object(LocalTrack, "isrc", isrc_prop),
        ):
            track.embed_match(match)

        set_calls = [c for c in isrc_prop.call_args_list if c.args]
        assert len(set_calls) == 0

    def test_embed_match_normalizes_hyphenated_isrc_from_match(self) -> None:
        track = self._make_local_track(MagicMock())
        match = self._make_service_track_mock(isrc="US-RC1-76-07839")
        isrc_prop = PropertyMock(return_value=None)

        with (
            patch.object(LocalTrack, "service_ref", return_value=match.permalink),
            patch.object(LocalTrack, "isrc", isrc_prop),
        ):
            track.embed_match(match)

        set_calls = [c for c in isrc_prop.call_args_list if c.args]
        assert len(set_calls) == 1
        assert set_calls[0].args[0] == "USRC17607839"


# ---------------------------------------------------------------------------
# T007: TestLocalTrackServiceRefCoexistence — multi-service independence
# ---------------------------------------------------------------------------


class TestLocalTrackServiceRefCoexistence(_LocalTrackTestBase):
    """Tests that multiple service refs coexist independently in the same track."""

    def test_service_ref_returns_none_for_unknown_service(self) -> None:
        track = self._make_local_track(MagicMock())
        with patch.object(LocalTrack, "_get_custom_tag", return_value=None):
            result = track.service_ref("UNKNOWN_SERVICE")
        assert result is None

    def test_embed_match_does_not_overwrite_different_service_ref(self) -> None:
        from tracks import ServiceTrack

        track = self._make_local_track(MagicMock())
        match = Mock(spec=ServiceTrack)
        match.service_name = "SPOTIFY"
        match.permalink = "https://open.spotify.com/track/abc123"
        match.isrc = None

        written: dict[str, str] = {}

        def fake_set_custom_tag(tag_name: str, value: str) -> None:
            written[tag_name] = value

        with (
            patch.object(LocalTrack, "service_ref", return_value=None),
            patch.object(track, "_set_custom_tag", side_effect=fake_set_custom_tag),
        ):
            track.embed_match(match)

        assert "SPOTIFY" in written
        assert "DEEZER" not in written

    def test_two_service_refs_coexist_independently(self) -> None:
        from tracks import ServiceTrack

        track = self._make_local_track(MagicMock())
        stored: dict[str, str] = {}

        def fake_get_custom_tag(tag_name: str) -> str | None:
            return stored.get(tag_name.upper())

        def fake_set_custom_tag(tag_name: str, value: str) -> None:
            stored[tag_name.upper()] = value

        spotify_match = Mock(spec=ServiceTrack)
        spotify_match.service_name = "SPOTIFY"
        spotify_match.permalink = "https://open.spotify.com/track/sp1"
        spotify_match.isrc = None

        deezer_match = Mock(spec=ServiceTrack)
        deezer_match.service_name = "DEEZER"
        deezer_match.permalink = "https://www.deezer.com/track/dz1"
        deezer_match.isrc = None

        with (
            patch.object(track, "_get_custom_tag", side_effect=fake_get_custom_tag),
            patch.object(track, "_set_custom_tag", side_effect=fake_set_custom_tag),
        ):
            track.embed_match(spotify_match)
            track.embed_match(deezer_match)

        assert stored.get("SPOTIFY") == "https://open.spotify.com/track/sp1"
        assert stored.get("DEEZER") == "https://www.deezer.com/track/dz1"


# ---------------------------------------------------------------------------
# T009: TestTrackContracts — LocalTrack isinstance checks
# ---------------------------------------------------------------------------


class TestTrackContracts(_LocalTrackTestBase):
    """Verify LocalTrack satisfies EmbeddableTrack but not ServiceTrack."""

    def test_local_track_is_embeddable_track(self) -> None:
        from tracks import EmbeddableTrack

        track = self._make_local_track(MagicMock())
        assert isinstance(track, EmbeddableTrack)

    def test_local_track_is_not_service_track(self) -> None:
        from tracks import ServiceTrack

        track = self._make_local_track(MagicMock())
        assert not isinstance(track, ServiceTrack)
