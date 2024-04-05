import click

from playlists.local_playlist import LocalPlaylist
from playlists.spotify_playlist import SpotifyPlaylist


@click.group()
def cli():
    pass


@cli.group("spotify")
def cli_spotify():
    pass


@cli_spotify.command("import")
@click.option("--source", "-s", required=True, multiple=True, help="Source playlist path")
@click.option("--destination", "-d", required=True, multiple=True, help="Destination playlist name")
@click.option("--autopilot", is_flag=True, help="When multiple matches are found, choose the first one")
@click.option("--embed-matches", is_flag=True, help="Embed a reference to the matched track in the source track")
def cli_spotify_import(source, destination, autopilot: bool = False, embed_matches: bool = False):
    if len(source) != len(destination):
        raise click.BadParameter("Number of sources must match the number of destinations")
    inputs = zip(source, destination)
    for source, destination in inputs:
        playlist = LocalPlaylist(source)
        SpotifyPlaylist.create_from_another_playlist(destination, playlist, autopilot=autopilot,
                                                     embed_matches=embed_matches)


@cli_spotify.command("match")
@click.option("--source", "-s", required=True, multiple=True, help="Source playlist path")
@click.option("--autopilot", is_flag=True, help="When multiple matches are found, choose the first one")
def cli_spotify_match(source, autopilot: bool = False):
    for source in source:
        playlist = LocalPlaylist(source)
        SpotifyPlaylist.track_matcher().match_list(playlist.tracks, autopilot=autopilot, embed_matches=True)


if __name__ == "__main__":
    cli()
