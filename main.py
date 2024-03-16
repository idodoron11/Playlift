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

spotify_tracks = SpotifyTrack.search("Asaf Avidan", "Different Pulses", "Different Pulses")
for track in spotify_tracks:
    print(track.title)
    print(track.display_artist)
    print(track.album)
