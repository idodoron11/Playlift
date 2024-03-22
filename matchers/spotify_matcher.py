from typing import Iterable, Optional, List

import click

from api.spotify import SpotifyAPI
from matchers import Matcher
from tqdm import tqdm
from tracks import Track
from tracks.spotify_track import SpotifyTrack


class SpotifyMatcher(Matcher):
    def match(self, track: Track) -> Optional[SpotifyTrack]:
        for artist in track.artists:
            explicit_search_string = f'artist:"{artist}" album:"{track.album}" track:"{track.title}"'
            results = SpotifyMatcher._search(explicit_search_string)
            if results:
                return results[0]
        return None

    def suggest_match(self, track: Track) -> Iterable[SpotifyTrack]:
        results_set = set()
        for artist in track.artists:
            search_string = f'{artist} {track.title}'
            results_set.update(SpotifyMatcher._search(search_string))
        results: List[SpotifyTrack] = list(results_set)
        results.sort(key=lambda result: SpotifyMatcher.track_distance(track, result))
        return results

    @staticmethod
    def _search(query: str) -> List[SpotifyTrack]:
        response = SpotifyAPI.get_instance().search(query)
        if not response['tracks'] or response['tracks']['total'] == 0:
            return []
        return [SpotifyTrack(track['id'], data=track) for track in response['tracks']['items']]

    def match_list(self, tracks: Iterable[Track]) -> List[Iterable[SpotifyTrack]]:
        tracks = list(tracks)
        sp_tracks: List[Iterable[SpotifyTrack]] = []
        guessed_tracks_positions: List[(int, Iterable[SpotifyTrack])] = []
        for index, track in enumerate(tqdm(tracks)):
            match = self.match(track)
            if match:
                sp_tracks.append([match])
                continue
            suggestions = self.suggest_match(track)
            if suggestions:
                sp_tracks.append(suggestions)

        # if len(guessed_tracks_positions) > 0:
        #     print("The following tracks were guessed:\n")
        #     for index, _ in guessed_tracks_positions:
        #         source: Track = tracks[index]
        #         target: SpotifyTrack = sp_tracks[index]
        #         print(
        #             f"{index + 1} {source.display_artist} - {source.title}, {source.album}    --->    {target.display_artist} - {target.title}, {target.album}")
        #     print("\nIf any of the tracks above were not mapped correctly, you have an opportunity to remove them")
        #     indices_str = click.prompt("Enter all the indices of tracks you wish to remove, separated by comma", default="")
        #     if len(indices_str.strip()) > 0:
        #         indices = set(map(lambda index_str: int(index_str.strip()) - 1, indices_str.split(",")))
        #         return [track for index, track in enumerate(sp_tracks) if index not in indices]

        return sp_tracks
