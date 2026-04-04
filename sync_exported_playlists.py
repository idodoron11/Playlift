#!/usr/bin/env python3

import subprocess
import sys
from pathlib import Path

import click


@click.command()
@click.argument("path", type=click.Path(exists=True, file_okay=True, dir_okay=True, path_type=Path))
def sync_playlists(path: Path) -> None:
    """
    Scans a directory recursively for .m3u files and imports them into Spotify.
    The playlist name is inferred from the file name.
    """
    # Find all .m3u files recursively
    if path.is_dir():
        playlist_files = list(path.rglob("*.m3u"))
    else:
        playlist_files = [path]

    if not playlist_files:
        click.echo("No .m3u files found in the specified directory.")
        return

    click.echo(f"Found {len(playlist_files)} playlist files:")
    for pf in playlist_files:
        click.echo(f"  {pf}")

    if not click.confirm("Do you want to import these playlists to Spotify?"):
        return

    # Convert paths to strings and create playlist names from filenames
    sources = [str(pf.absolute()) for pf in playlist_files]
    destinations = [pf.stem for pf in playlist_files]  # stem is the filename without extension

    # Create command line arguments
    cmd = [sys.executable, "main.py", "spotify", "import"]
    for src, dst in zip(sources, destinations):
        cmd.extend(["--source", src, "--destination", dst])

    # Run the command in a subprocess, inheriting stdin/stdout for interactivity
    try:
        subprocess.run(cmd, check=True)
        click.echo("Successfully imported playlists to Spotify!")
    except subprocess.CalledProcessError as e:
        click.echo(f"Error importing playlists. Exit code: {e.returncode}", err=True)
        raise click.Abort()


if __name__ == "__main__":
    sync_playlists()
