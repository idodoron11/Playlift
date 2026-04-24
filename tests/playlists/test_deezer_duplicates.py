"""Unit tests for deezer duplicates (T025)."""

from __future__ import annotations

from click.testing import CliRunner

from main import cli


class TestDeezerDuplicatesCli:
    def _run(self, m3u_content: str) -> str:

        runner = CliRunner()
        with runner.isolated_filesystem():
            with open("playlist.m3u", "w") as f:
                f.write(m3u_content)
            result = runner.invoke(cli, ["deezer", "duplicates", "--source", "playlist.m3u"])
            return result.output

    def test_two_tracks_with_same_deezer_ref_reported(self) -> None:
        """Two tracks sharing the same TXXX:DEEZER value appear as duplicates."""
        from unittest.mock import MagicMock, patch

        from tracks.local_track import LocalTrack

        runner = CliRunner()

        def _make_local_track(path: str, ref: str) -> MagicMock:
            t = MagicMock(spec=LocalTrack)
            t.file_path = path
            t.service_ref.return_value = ref
            return t

        track_a = _make_local_track("/music/a.mp3", "https://www.deezer.com/track/99")
        track_b = _make_local_track("/music/b.mp3", "https://www.deezer.com/track/99")

        with (
            patch("main.get_playlist") as mock_gp,
        ):
            mock_playlist = MagicMock()
            mock_playlist.tracks = [track_a, track_b]
            mock_gp.return_value = mock_playlist

            result = runner.invoke(cli, ["deezer", "duplicates", "--source", "fake.m3u"])

        assert "Duplicate Deezer references found:" in result.output
        assert "https://www.deezer.com/track/99" in result.output

    def test_playlist_with_no_duplicates_produces_clean_output(self) -> None:
        from unittest.mock import MagicMock, patch

        from tracks.local_track import LocalTrack

        runner = CliRunner()

        def _make_local_track(path: str, ref: str) -> MagicMock:
            t = MagicMock(spec=LocalTrack)
            t.file_path = path
            t.service_ref.return_value = ref
            return t

        track_a = _make_local_track("/music/a.mp3", "https://www.deezer.com/track/1")
        track_b = _make_local_track("/music/b.mp3", "https://www.deezer.com/track/2")

        with patch("main.get_playlist") as mock_gp:
            mock_playlist = MagicMock()
            mock_playlist.tracks = [track_a, track_b]
            mock_gp.return_value = mock_playlist

            result = runner.invoke(cli, ["deezer", "duplicates", "--source", "fake.m3u"])

        assert "Duplicate" not in result.output
