from playlists.local_playlist import LocalPlaylist
from playlists.spotify_playlist import SpotifyPlaylist
from tracks.spotify_track import SpotifyTrack

playlist = LocalPlaylist("/Users/idodoron/Downloads/Seasons_of_change.m3u")
sp_playlist = SpotifyPlaylist.create("idodo test")
sp_tracks = []
for index, track in enumerate(playlist.tracks):
    response = SpotifyTrack.search(track.artists[0], track.album, track.title)
    sp_track = response[0]
    sp_tracks.append(sp_track)
    if sp_tracks:
        print(f"{index+1} {track.display_artist} - {track.title} ---> {sp_track.display_artist} - {sp_track.title} ({sp_track.album})")
sp_playlist.add_tracks(sp_tracks)

