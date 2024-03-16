from playlists.spotify_playlist import SpotifyPlaylist

playlist = SpotifyPlaylist("https://open.spotify.com/playlist/7D3hTu62FCcQCscv6xzjRB")
for index, track in enumerate(playlist.tracks):
    print(f"{index} {track.display_artist} - {track.title} ({track.album})")