from playlists.local_playlist import LocalPlaylist
from tracks.spotify_track import SpotifyTrack

playlist = LocalPlaylist("/Users/idodoron/Downloads/Seasons_of_change.m3u")
for index, track in enumerate(playlist.tracks):
    sp_tracks = SpotifyTrack.search(track.artists[0], track.album, track.title)
    if sp_tracks:
        print(f"{index+1} {track.display_artist} - {track.title} ---> {sp_tracks[0].display_artist} - {sp_tracks[0].title} ({sp_tracks[0].album})")
