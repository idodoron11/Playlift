import config
from api.spotify import SpotifyAPI
from providers.local_playlist import LocalPlaylist
from tracks.spotify_track import SpotifyTrack

playlist = LocalPlaylist("/Users/idodoron/Downloads/Seasons_of_change.m3u")
for track in playlist.tracks:
    print(track.title)
    print(track.display_artist)
    print(track.album)
    print(track.duration)
spotify_api = SpotifyAPI().api

spotify_track = SpotifyTrack("http://open.spotify.com/track/6rqhFgbbKwnb9MLmUQDhG6")
print(spotify_track.title)
print(spotify_track.display_artist)
print(spotify_track.album)
