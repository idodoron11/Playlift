"""Tests for loading callback wiring in LocalPlaylist."""

from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import MagicMock, patch

import mutagen

from playlists.local_playlist import LocalPlaylist

if TYPE_CHECKING:
    from pathlib import Path


def _write_m3u(tmp_path: Path, entries: list[str]) -> str:
    m3u = tmp_path / "playlist.m3u"
    m3u.write_text("\n".join(entries), encoding="utf-8")
    return str(m3u)


class TestLocalPlaylistCallbacks:
    def test_on_loading_started_called_with_track_count(self, tmp_path: Path) -> None:
        path = _write_m3u(tmp_path, ["/fake/a.mp3", "/fake/b.mp3", "/fake/c.mp3"])
        on_started = MagicMock()
        with patch("playlists.local_playlist.LocalTrack"):
            LocalPlaylist(path, on_loading_started=on_started)
        on_started.assert_called_once_with(3)

    def test_on_track_loaded_called_once_per_file(self, tmp_path: Path) -> None:
        path = _write_m3u(tmp_path, ["/fake/a.mp3", "/fake/b.mp3", "/fake/c.mp3"])
        on_loaded = MagicMock()
        with patch("playlists.local_playlist.LocalTrack"):
            LocalPlaylist(path, on_track_loaded=on_loaded)
        assert on_loaded.call_count == 3

    def test_on_track_loaded_called_even_on_mutagen_error(self, tmp_path: Path) -> None:
        path = _write_m3u(tmp_path, ["/fake/a.mp3", "/fake/b.mp3"])
        on_loaded = MagicMock()
        with patch("playlists.local_playlist.LocalTrack", side_effect=mutagen.MutagenError):  # type: ignore[attr-defined]
            LocalPlaylist(path, on_track_loaded=on_loaded)
        assert on_loaded.call_count == 2

    def test_no_callbacks_does_not_raise(self, tmp_path: Path) -> None:
        path = _write_m3u(tmp_path, ["/fake/a.mp3"])
        with patch("playlists.local_playlist.LocalTrack"):
            LocalPlaylist(path)  # no callbacks — must not raise

    def test_on_loading_started_called_with_zero_for_empty_playlist(self, tmp_path: Path) -> None:
        path = _write_m3u(tmp_path, [])
        on_started = MagicMock()
        on_loaded = MagicMock()
        with patch("playlists.local_playlist.LocalTrack"):
            LocalPlaylist(path, on_loading_started=on_started, on_track_loaded=on_loaded)
        on_started.assert_called_once_with(0)
        on_loaded.assert_not_called()
