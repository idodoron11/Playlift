from difflib import SequenceMatcher

import click
from spotipy import SpotifyException
from tabulate import tabulate
from tqdm import tqdm

from matchers.spotify_matcher import SpotifyMatcher
from playlists.local_playlist import LocalPlaylist
from tracks.local_track import LocalTrack
from tracks.spotify_track import SpotifyTrack


def rematch(track: LocalTrack):
    search_results = matcher._search(f"{track.title} {track.display_artist}")
    print(f'Please choose the best match for\n{track}')
    print("If none match, type -1")
    headers = ["#", "Artist", "Track Title", "Album", "Track Position", "Duration"]
    data = [(pos, sp_track.display_artist, sp_track.title, sp_track.album, sp_track.track_number, sp_track.duration)
            for pos, sp_track in enumerate(search_results)]
    results_tbl_visual = tabulate(data, headers=headers)
    print(results_tbl_visual)

    while True:
        choice = click.prompt("Enter best match index (#), or enter a custom track ID")
        try:
            choice = int(choice)
            if choice < 0 or choice >= len(search_results):
                print("Skipping track")
            sp_track = search_results[choice]
            break
        except ValueError:
            pass
        try:
            sp_track = SpotifyTrack(choice)
            break
        except SpotifyException:
            print("Invalid input")
    track.spotify_ref = sp_track.track_url


playlist_path = click.prompt("Enter playlist path")
matcher = SpotifyMatcher.get_instance()

playlist = LocalPlaylist(playlist_path)
for index, track in enumerate(tqdm(playlist.tracks)):
    spotify_ref = track.spotify_ref
    if not spotify_ref or spotify_ref == "SKIP":
        continue
    spotify_track = SpotifyTrack(spotify_ref)
    simplified_track_title = track.title.lower().replace(" - ", " ").replace("(", "").replace(")", "")
    simplified_spotify_track_title = spotify_track.title.lower().replace(" - ", " ").replace("(", "").replace(")", "")
    if SequenceMatcher(None, simplified_track_title, simplified_spotify_track_title).ratio() < 0.9:
        print(f"Local track: {track}")
        print(f"Spotify track: {spotify_track}")
        replace = click.confirm("Replace match?", default=False)
        if replace:
            rematch(track)
