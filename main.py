from providers.local_playlist import LocalPlaylist

playlist = LocalPlaylist("/Users/idodoron/Downloads/Seasons_of_change.m3u")
for track in playlist.tracks:
    print(track.title)
    print(track.artists)
    print(track.album)
    print(track.duration)
