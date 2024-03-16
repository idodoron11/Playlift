import config
from api.spotify import SpotifyAPI
from providers.local_playlist import LocalPlaylist

playlist = LocalPlaylist("/Users/idodoron/Downloads/Seasons_of_change.m3u")
for track in playlist.tracks:
    print(track.title)
    print(track.display_artist)
    print(track.album)
    print(track.duration)
spotify_api = SpotifyAPI().api

results = spotify_api.current_user_saved_tracks()
for idx, item in enumerate(results['items']):
    track = item['track']
    print(idx, track['artists'][0]['name'], " – ", track['name'])
