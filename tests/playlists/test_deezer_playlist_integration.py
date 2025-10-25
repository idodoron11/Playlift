"""Integration tests for DeezerPlaylist with real Deezer API."""
from playlists.deezer_playlist import DeezerPlaylist
from tracks.deezer_track import DeezerTrack


def test_read_real_playlist():
    """Test reading a real Deezer playlist."""
    playlist_url = "https://www.deezer.com/en/playlist/7211464104"
    playlist = DeezerPlaylist(playlist_url)

    print(f"\nPlaylist: {playlist.name}")
    print("Tracks:")
    for i, track in enumerate(playlist.tracks, 1):
        print(f"{i}. {track.artist} - {track.title} ({track.album})")

if __name__ == '__main__':
    test_read_real_playlist()
