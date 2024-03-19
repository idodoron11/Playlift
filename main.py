import click

from matchers.spotify_matcher import SpotifyMatcher
from playlists.local_playlist import LocalPlaylist
from playlists.spotify_playlist import SpotifyPlaylist
from tracks import Track
from tracks.spotify_track import SpotifyTrack
from tqdm import tqdm


@click.group()
def cli():
    pass


@cli.group("spotify")
def cli_spotify():
    pass


@cli_spotify.command("import")
@click.argument("source")
@click.argument("destination")
def cli_spotify_import(source, destination):
    playlist = LocalPlaylist(source)
    sp_tracks = []
    guessed_tracks_positions = []
    for index, track in enumerate(tqdm(playlist.tracks)):
        match = SpotifyMatcher.get_instance().match(track)
        if match:
            sp_tracks.append(match)
            continue
        suggestions = SpotifyMatcher.get_instance().suggest_match(track)
        if suggestions:
            sp_tracks.append(suggestions[0])
            guessed_tracks_positions.append(index)
    print("The following tracks were guessed:\n")
    for index in guessed_tracks_positions:
        source: Track = playlist.tracks[index]
        target: SpotifyTrack = sp_tracks[index]
        print(f"{index} {source.display_artist} - {source.title}, {source.album}    --->    {target.display_artist} - {target.title}, {target.album}")
    sp_playlist = SpotifyPlaylist.create(destination)
    sp_playlist.add_tracks(sp_tracks)


if __name__ == "__main__":
    cli()
