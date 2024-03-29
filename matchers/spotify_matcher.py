from typing import Iterable, Optional, List

import click

from api.spotify import SpotifyAPI
from matchers import Matcher
from tqdm import tqdm
from tracks import Track
from tracks.spotify_track import SpotifyTrack


class SpotifyMatcher(Matcher):
    def match(self, track: Track) -> Optional[SpotifyTrack]:
        artist_components = [f'artist:"{artist}"' for artist in track.artists] if track.artists else [""]
        album_component = f'album:"{track.album}"' if track.album else ""
        title_component = f'track:"{track.title}"' if track.title else ""
        for artist_component in artist_components:
            explicit_search_string = " ".join((artist_component, album_component, title_component))
            if not explicit_search_string.strip():
                return None
            results = SpotifyMatcher._search(explicit_search_string)
            if results:
                return results[0]
        return None

    @staticmethod
    def _match_constraints(source_track: Track, suggestion: SpotifyTrack) -> bool:
        title_d, artist_d, album_d, duration_d = SpotifyMatcher.track_distance(source_track, suggestion)
        title_d = 1 - title_d
        artist_d = 1 - artist_d
        album_d = 1 - album_d

        def is_latin(text: str) -> bool:
            return all(not char.isalpha() or ord('a') <= ord(char.lower()) <= ord('z') for char in text)

        return (title_d >= 0.5 and
                (not is_latin(source_track.display_artist) or artist_d >= 0.5)
                and album_d >= 0.5
                and duration_d <= 5)

    def suggest_match(self, track: Track) -> Iterable[SpotifyTrack]:
        results_set = set()
        for artist in track.artists:
            search_string = f'{artist} {track.title}'
            results_set.update(SpotifyMatcher._search(search_string))

        results: List[SpotifyTrack] = list(
            filter(lambda result: SpotifyMatcher._match_constraints(track, result), results_set)
        )
        results.sort(key=lambda result: SpotifyMatcher.track_distance(track, result))

        for result in results:
            if set(result.artists) == set(track.artists) and result.album == track.album and result.track_number == track.track_number:
                return [result]

        return results

    @staticmethod
    def _search(query: str) -> List[SpotifyTrack]:
        response = SpotifyAPI.get_instance().search(query, limit=None)
        if not response['tracks'] or response['tracks']['total'] == 0:
            return []
        return [SpotifyTrack(track['id'], data=track) for track in response['tracks']['items']]

    def match_list(self, tracks: Iterable[Track]) -> List[Iterable[SpotifyTrack]]:
        tracks = list(tracks)
        sp_tracks: List[Iterable[SpotifyTrack]] = []
        print("Matching source tracks to Spotify tracks")
        for index, track in enumerate(tqdm(tracks)):
            match = self.match(track)
            if match:
                sp_tracks.append([match])
                continue
            suggestions = self.suggest_match(track)
            sp_tracks.append(suggestions)
        return sp_tracks
