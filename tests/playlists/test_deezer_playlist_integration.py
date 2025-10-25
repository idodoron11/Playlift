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


def test_copy_playlist():
    """Test copying an existing Deezer playlist to a new one."""
    # Read the source playlist
    source_playlist = DeezerPlaylist("https://www.deezer.com/en/playlist/7211464104")
    source_name = source_playlist.name

    # Create a new playlist with the same name
    new_playlist = DeezerPlaylist.create(f"{source_name} (Copy)")

    # Get all tracks from source playlist
    tracks = list(source_playlist.tracks)

    # Add tracks to the new playlist
    success = new_playlist.add_tracks(tracks)

    print(f"\nCreated new playlist: {new_playlist.name}")
    print(f"New playlist ID: {new_playlist.playlist_id}")
    print(f"New playlist URL: https://www.deezer.com/playlist/{new_playlist.playlist_id}")
    print(f"Track copy {'succeeded' if success else 'failed'}")


if __name__ == '__main__':
    test_read_real_playlist()
    # test_copy_playlist()
