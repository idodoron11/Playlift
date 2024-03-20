from typing import Iterable, Optional, List

from api.spotify import SpotifyAPI
from matchers import Matcher
from difflib import SequenceMatcher
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
        return [SpotifyTrack(track['id']) for track in response['tracks']['items']]

