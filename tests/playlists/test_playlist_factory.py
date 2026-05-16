"""Unit tests for PlaylistFactory.resolve()."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from exceptions import InvalidPathMappingError, UnrecognisedSourceError
from playlists.playlist_factory import PlaylistFactory

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def factory() -> PlaylistFactory:
    """Return a PlaylistFactory with mock clients."""
    spotify_client = MagicMock()
    deezer_client = MagicMock()
    return PlaylistFactory(spotify_client=spotify_client, deezer_client=deezer_client)


# ---------------------------------------------------------------------------
# T004 — Service source dispatch (US1 core cases)
# ---------------------------------------------------------------------------


class TestResolveSpotifyUri:
    def test_returns_spotify_playlist_for_spotify_uri(self, factory: PlaylistFactory) -> None:
        uri = "spotify:playlist:37i9dQZF1DXcBWIGoYBM5M"
        with patch("playlists.playlist_factory.SpotifyPlaylist") as mock_spotify:
            result = factory.resolve(uri)
        mock_spotify.assert_called_once_with(uri, client=factory._spotify_client)
        assert result is mock_spotify.return_value

    def test_returns_spotify_playlist_for_https_url(self, factory: PlaylistFactory) -> None:
        url = "https://open.spotify.com/playlist/37i9dQZF1DXcBWIGoYBM5M?si=abc"
        with patch("playlists.playlist_factory.SpotifyPlaylist") as mock_spotify:
            result = factory.resolve(url)
        mock_spotify.assert_called_once_with(url, client=factory._spotify_client)
        assert result is mock_spotify.return_value


class TestResolveDeezerUrl:
    def test_returns_deezer_playlist_for_deezer_url(self, factory: PlaylistFactory) -> None:
        url = "https://www.deezer.com/en/playlist/1234567890"
        with patch("playlists.playlist_factory.DeezerPlaylist") as mock_deezer:
            result = factory.resolve(url)
        mock_deezer.assert_called_once_with("1234567890", deezer=factory._deezer_client)
        assert result is mock_deezer.return_value

    def test_extracts_numeric_id_from_deezer_url(self, factory: PlaylistFactory) -> None:
        url = "https://deezer.com/playlist/9876543210"
        with patch("playlists.playlist_factory.DeezerPlaylist") as mock_deezer:
            factory.resolve(url)
        mock_deezer.assert_called_once_with("9876543210", deezer=factory._deezer_client)

    def test_extracts_id_from_deezer_url_with_locale(self, factory: PlaylistFactory) -> None:
        url = "https://www.deezer.com/fr/playlist/1111111111?utm_source=deezer"
        with patch("playlists.playlist_factory.DeezerPlaylist") as mock_deezer:
            factory.resolve(url)
        mock_deezer.assert_called_once_with("1111111111", deezer=factory._deezer_client)


class TestResolvePathMapperGuard:
    def test_raises_invalid_path_mapping_error_for_spotify_uri_with_path_mapper(self, factory: PlaylistFactory) -> None:
        path_mapper = MagicMock()
        with pytest.raises(InvalidPathMappingError):
            factory.resolve("spotify:playlist:abc123", path_mapper=path_mapper)

    def test_raises_invalid_path_mapping_error_for_spotify_url_with_path_mapper(self, factory: PlaylistFactory) -> None:
        path_mapper = MagicMock()
        with pytest.raises(InvalidPathMappingError):
            factory.resolve("https://open.spotify.com/playlist/abc123", path_mapper=path_mapper)

    def test_raises_invalid_path_mapping_error_for_deezer_url_with_path_mapper(self, factory: PlaylistFactory) -> None:
        path_mapper = MagicMock()
        with pytest.raises(InvalidPathMappingError):
            factory.resolve("https://www.deezer.com/en/playlist/123456", path_mapper=path_mapper)


class TestResolveUnrecognised:
    def test_raises_unrecognised_source_error_for_garbage_string(self, factory: PlaylistFactory) -> None:
        with pytest.raises(UnrecognisedSourceError):
            factory.resolve("not-a-valid-source")

    def test_raises_unrecognised_source_error_for_nonexistent_path(self, factory: PlaylistFactory) -> None:
        with pytest.raises(UnrecognisedSourceError):
            factory.resolve("/does/not/exist/playlist.m3u")

    def test_raises_unrecognised_source_error_when_deezer_client_is_none(self) -> None:
        factory_no_deezer = PlaylistFactory(spotify_client=MagicMock(), deezer_client=None)
        with pytest.raises(UnrecognisedSourceError, match="no authenticated Deezer client"):
            factory_no_deezer.resolve("https://www.deezer.com/en/playlist/123")

    def test_raises_unrecognised_source_error_when_spotify_client_is_none(self) -> None:
        factory_no_spotify = PlaylistFactory(spotify_client=None, deezer_client=MagicMock())
        with pytest.raises(UnrecognisedSourceError, match="no authenticated Spotify client"):
            factory_no_spotify.resolve("spotify:playlist:abc123")


# ---------------------------------------------------------------------------
# T017 — All six source x destination dispatch paths
# ---------------------------------------------------------------------------


class TestResolveAllSourceFormats:
    @pytest.mark.parametrize(
        ("source", "expected_class_name"),
        [
            ("spotify:playlist:abc123", "SpotifyPlaylist"),
            ("https://open.spotify.com/playlist/abc123", "SpotifyPlaylist"),
            ("https://www.deezer.com/en/playlist/111", "DeezerPlaylist"),
            ("https://deezer.com/playlist/222", "DeezerPlaylist"),
        ],
    )
    def test_service_source_returns_correct_type(
        self, factory: PlaylistFactory, source: str, expected_class_name: str
    ) -> None:
        with (
            patch("playlists.playlist_factory.SpotifyPlaylist") as mock_spotify,
            patch("playlists.playlist_factory.DeezerPlaylist") as mock_deezer,
        ):
            mock_spotify.__name__ = "SpotifyPlaylist"
            mock_deezer.__name__ = "DeezerPlaylist"
            result = factory.resolve(source)
        if expected_class_name == "SpotifyPlaylist":
            assert result is mock_spotify.return_value
        else:
            assert result is mock_deezer.return_value

    def test_local_file_returns_local_playlist(
        self, factory: PlaylistFactory, tmp_path: pytest.TempPathFactory
    ) -> None:
        m3u_file = tmp_path / "test.m3u"  # type: ignore[operator]
        m3u_file.write_text("#EXTM3U\n")
        with patch("playlists.playlist_factory.LocalPlaylist") as mock_local:
            result = factory.resolve(str(m3u_file))
        mock_local.assert_called_once_with(
            str(m3u_file), path_mapper=None, on_loading_started=None, on_track_loaded=None
        )
        assert result is mock_local.return_value

    def test_local_directory_returns_local_library(
        self, factory: PlaylistFactory, tmp_path: pytest.TempPathFactory
    ) -> None:
        with patch("playlists.playlist_factory.LocalLibrary") as mock_lib:
            result = factory.resolve(str(tmp_path))
        mock_lib.assert_called_once_with(str(tmp_path), on_loading_started=None, on_track_loaded=None)
        assert result is mock_lib.return_value


# ---------------------------------------------------------------------------
# T009 — US2 sync-command symmetry (same dispatch, different calling context)
# ---------------------------------------------------------------------------


class TestResolveSymmetryForSyncCommands:
    """Confirm resolve() behaves identically regardless of whether caller is
    an import or sync command — the factory does not know the difference."""

    def test_spotify_uri_dispatch_is_identical_for_sync_context(self, factory: PlaylistFactory) -> None:
        uri = "spotify:playlist:synctest"
        with patch("playlists.playlist_factory.SpotifyPlaylist") as mock_spotify:
            result = factory.resolve(uri)
        mock_spotify.assert_called_once_with(uri, client=factory._spotify_client)
        assert result is mock_spotify.return_value

    def test_spotify_url_dispatch_is_identical_for_sync_context(self, factory: PlaylistFactory) -> None:
        url = "https://open.spotify.com/playlist/synctest"
        with patch("playlists.playlist_factory.SpotifyPlaylist") as mock_spotify:
            result = factory.resolve(url)
        mock_spotify.assert_called_once_with(url, client=factory._spotify_client)
        assert result is mock_spotify.return_value

    def test_deezer_url_dispatch_is_identical_for_sync_context(self, factory: PlaylistFactory) -> None:
        url = "https://www.deezer.com/en/playlist/42"
        with patch("playlists.playlist_factory.DeezerPlaylist") as mock_deezer:
            result = factory.resolve(url)
        mock_deezer.assert_called_once_with("42", deezer=factory._deezer_client)
        assert result is mock_deezer.return_value


# ---------------------------------------------------------------------------
# T011 — US3 regression: local workflow paths
# ---------------------------------------------------------------------------


class TestResolveLocalRegressions:
    def test_local_m3u_without_path_mapper(self, factory: PlaylistFactory, tmp_path: pytest.TempPathFactory) -> None:
        m3u_file = tmp_path / "music.m3u"  # type: ignore[operator]
        m3u_file.write_text("#EXTM3U\n")
        with patch("playlists.playlist_factory.LocalPlaylist") as mock_local:
            result = factory.resolve(str(m3u_file))
        mock_local.assert_called_once_with(
            str(m3u_file), path_mapper=None, on_loading_started=None, on_track_loaded=None
        )
        assert result is mock_local.return_value

    def test_local_m3u_with_path_mapper(self, factory: PlaylistFactory, tmp_path: pytest.TempPathFactory) -> None:
        m3u_file = tmp_path / "music.m3u"  # type: ignore[operator]
        m3u_file.write_text("#EXTM3U\n")
        path_mapper = MagicMock()
        with patch("playlists.playlist_factory.LocalPlaylist") as mock_local:
            result = factory.resolve(str(m3u_file), path_mapper=path_mapper)
        mock_local.assert_called_once_with(
            str(m3u_file), path_mapper=path_mapper, on_loading_started=None, on_track_loaded=None
        )
        assert result is mock_local.return_value

    def test_local_directory_without_path_mapper(
        self, factory: PlaylistFactory, tmp_path: pytest.TempPathFactory
    ) -> None:
        with patch("playlists.playlist_factory.LocalLibrary") as mock_lib:
            result = factory.resolve(str(tmp_path))
        mock_lib.assert_called_once_with(str(tmp_path), on_loading_started=None, on_track_loaded=None)
        assert result is mock_lib.return_value

    def test_path_mapper_forwarded_correctly_for_local_source(
        self, factory: PlaylistFactory, tmp_path: pytest.TempPathFactory
    ) -> None:
        m3u_file = tmp_path / "another.m3u"  # type: ignore[operator]
        m3u_file.write_text("#EXTM3U\n")
        path_mapper = MagicMock()
        with patch("playlists.playlist_factory.LocalPlaylist") as mock_local:
            factory.resolve(str(m3u_file), path_mapper=path_mapper)
        _, kwargs = mock_local.call_args
        assert kwargs["path_mapper"] is path_mapper

    def test_callbacks_forwarded_to_local_playlist(
        self, factory: PlaylistFactory, tmp_path: pytest.TempPathFactory
    ) -> None:
        m3u_file = tmp_path / "cb.m3u"  # type: ignore[operator]
        m3u_file.write_text("#EXTM3U\n")
        on_start = MagicMock()
        on_loaded = MagicMock()
        with patch("playlists.playlist_factory.LocalPlaylist") as mock_local:
            factory.resolve(str(m3u_file), on_loading_started=on_start, on_track_loaded=on_loaded)
        _, kwargs = mock_local.call_args
        assert kwargs["on_loading_started"] is on_start
        assert kwargs["on_track_loaded"] is on_loaded

    def test_callbacks_forwarded_to_local_library(
        self, factory: PlaylistFactory, tmp_path: pytest.TempPathFactory
    ) -> None:
        on_start = MagicMock()
        on_loaded = MagicMock()
        with patch("playlists.playlist_factory.LocalLibrary") as mock_lib:
            factory.resolve(str(tmp_path), on_loading_started=on_start, on_track_loaded=on_loaded)
        _, kwargs = mock_lib.call_args
        assert kwargs["on_loading_started"] is on_start
        assert kwargs["on_track_loaded"] is on_loaded
