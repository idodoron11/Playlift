import logging
import re
from collections.abc import Iterable

import spotipy
from tqdm import tqdm

from exceptions import SkipTrackError
from matchers import Matcher
from tracks import Track
from tracks.local_track import LocalTrack, _normalize_isrc
from tracks.spotify_track import SpotifyTrack

ISRC_PATTERN: re.Pattern[str] = re.compile(r"^[A-Z]{2}[A-Z0-9]{3}[0-9]{7}$")
SPOTIFY_BATCH_SIZE: int = 50  # Spotify /tracks endpoint hard limit per request

logger = logging.getLogger(__name__)


def _is_valid_isrc(isrc: str | None) -> bool:
    """Check whether *isrc* matches the ISRC format (12-char uppercase alphanumeric)."""
    if not isrc:
        return False
    return ISRC_PATTERN.match(isrc) is not None


class SpotifyMatcher(Matcher):
    def __init__(  # type: ignore[no-any-unimported]  # spotipy ships no type stubs
        self, client: spotipy.Spotify | None = None
    ) -> None:
        super().__init__()
        if client is None:
            raise ValueError("client must be provided")
        self._client = client

    def _prefetch_isrc_data(self, matches: list[SpotifyTrack]) -> None:
        """Batch-fetch full track data for SpotifyTrack objects that lack ISRC.

        Mutates _data in-place on each match so subsequent .isrc reads are
        served from memory. Called before the embed loop in match_list.
        Tracks whose _data already contains external_ids.isrc are skipped.
        """
        needs_fetch = [m for m in matches if not (m._data and m._data.get("external_ids", {}).get("isrc"))]
        if not needs_fetch:
            return

        # De-duplicate: multiple SpotifyTrack objects may share the same ID
        id_to_tracks: dict[str, list[SpotifyTrack]] = {}
        for m in needs_fetch:
            id_to_tracks.setdefault(m.track_id, []).append(m)

        track_ids = list(id_to_tracks)
        for i in range(0, len(track_ids), SPOTIFY_BATCH_SIZE):
            batch = track_ids[i : i + SPOTIFY_BATCH_SIZE]
            try:
                response = self._client.tracks(batch)
            except Exception:
                logger.warning(
                    "Batch ISRC prefetch failed for %d track(s); ISRC will not be embedded for this batch",
                    len(batch),
                )
                continue

            for track_id, item in zip(batch, response.get("tracks", []), strict=False):
                if item is None:
                    logger.debug(
                        "Batch ISRC prefetch: track %s not available on Spotify, skipping ISRC",
                        track_id,
                    )
                    continue
                for sp_track in id_to_tracks[track_id]:
                    sp_track._data = item

    def _find_spotify_match_in_source_track(self, track: Track) -> str | None:
        if isinstance(track, LocalTrack):
            return track.spotify_ref
        return None

    def _update_spotify_match_in_source_track(self, source_track: Track, match: SpotifyTrack) -> None:
        if isinstance(source_track, LocalTrack):
            if source_track.spotify_ref != match.track_url:
                source_track.spotify_ref = match.track_url
            if match.isrc is not None and source_track.isrc != _normalize_isrc(match.isrc):
                source_track.isrc = _normalize_isrc(match.isrc)

    def match(self, track: Track) -> SpotifyTrack | None:
        ref = self._find_spotify_match_in_source_track(track)
        if ref == "SKIP":
            raise SkipTrackError
        elif ref:
            return SpotifyTrack(ref, client=self._client)

        return self._match_by_isrc(track) or self._match_by_fuzzy_search(track)

    def _match_by_isrc(self, track: Track) -> SpotifyTrack | None:
        """Look up a track by its ISRC code on Spotify."""
        if not _is_valid_isrc(track.isrc):
            logger.debug("No valid ISRC for '%s', skipping ISRC lookup", track.title)
            return None
        try:
            results = self._search(f"isrc:{track.isrc}")
            if results:
                logger.info("Matched '%s' via ISRC %s", track.title, track.isrc)
                return results[0]
        except Exception:
            logger.warning(
                "ISRC lookup failed for '%s' (ISRC %s), falling back to fuzzy search",
                track.title,
                track.isrc,
            )
        return None

    def _match_by_fuzzy_search(self, track: Track) -> SpotifyTrack | None:
        """Search Spotify using artist/album/title metadata."""
        artist_components = [f'artist:"{artist}"' for artist in track.artists] if track.artists else [""]
        album_component = f'album:"{track.album}"' if track.album else ""
        title_component = f'track:"{track.title}"' if track.title else ""
        for artist_component in artist_components:
            explicit_search_string = " ".join((artist_component, album_component, title_component))
            if not explicit_search_string.strip():
                return None
            results = self._search(explicit_search_string)
            if results:
                logger.info("Matched '%s' via fuzzy search", track.title)
                return results[0]
        return None

    @staticmethod
    def _match_constraints(source_track: Track, suggestion: SpotifyTrack) -> bool:
        title_d, artist_d, album_d, duration_d = SpotifyMatcher.track_distance(source_track, suggestion)
        title_d = 1 - title_d
        artist_d = 1 - artist_d
        album_d = 1 - album_d

        def is_latin(text: str) -> bool:
            return all(not char.isalpha() or ord("a") <= ord(char.lower()) <= ord("z") for char in text)

        if not is_latin(source_track.display_artist):
            artist_d = 1  # Spotify may not list the artist in the original language

        avg_d = (title_d + artist_d + album_d) / 3
        if avg_d > 0.6 and duration_d < 3:
            return True
        if (
            artist_d >= 0.75
            and album_d >= 0.75
            and source_track.track_number == suggestion.track_number
            and duration_d <= 3
        ):
            return True

        return title_d >= 0.5 and artist_d >= 0.5 and album_d >= 0.5 and duration_d <= 5

    def suggest_match(self, track: Track) -> list[SpotifyTrack]:
        results_set: set[SpotifyTrack] = set()
        for artist in track.artists:
            search_string = f"{artist} {track.title}"
            results_set.update(self._search(search_string))

        results: list[SpotifyTrack] = list(
            filter(lambda result: SpotifyMatcher._match_constraints(track, result), results_set)
        )
        results.sort(key=lambda result: SpotifyMatcher.track_distance(track, result))

        for result in results:
            if (
                set(result.artists) == set(track.artists)
                and result.album == track.album
                and result.track_number == track.track_number
            ):
                return [result]

        return results

    def _search(self, query: str) -> list[SpotifyTrack]:
        response = self._client.search(query, limit=50)
        if not response["tracks"] or not response["tracks"]["items"]:
            return []
        return [SpotifyTrack(track["id"], data=track, client=self._client) for track in response["tracks"]["items"]]

    def _match_list(self, tracks: Iterable[Track]) -> list[list[SpotifyTrack]]:
        tracks = list(tracks)
        sp_tracks: list[list[SpotifyTrack]] = []
        print("Matching source tracks to Spotify tracks")
        for _index, track in enumerate(tqdm(tracks)):
            try:
                match = self.match(track)
                if match:
                    sp_tracks.append([match])
                    continue
                suggestions = self.suggest_match(track)
                sp_tracks.append(suggestions)
                if not suggestions:
                    print(f"Could not match\n{track}")
                    continue
            except SkipTrackError:
                print(f"Skip track\n{track}")
                sp_tracks.append([])
                continue
        return sp_tracks

    def match_list(self, tracks: Iterable[Track], autopilot: bool = False, embed_matches: bool = False) -> list[Track]:
        suggestions_list: list[list[SpotifyTrack]] = self._match_list(tracks)
        processed: list[list[SpotifyTrack]] = list(map(list, suggestions_list))
        sp_tracks: list[Track] = []
        pairs_to_embed: list[tuple[Track, SpotifyTrack]] = []

        print("Reviewing matches")
        for _index, (track, suggestions) in tqdm(list(enumerate(zip(tracks, processed, strict=True)))):
            if len(suggestions) == 0:
                continue
            choice = 0
            if len(suggestions) > 1 and not autopilot:
                choice = Matcher.choose_suggestion(track, suggestions)
            if choice >= 0:
                sp_tracks.append(suggestions[choice])
                if embed_matches:
                    pairs_to_embed.append((track, suggestions[choice]))

        if pairs_to_embed:
            chosen_matches = [match for _, match in pairs_to_embed]
            self._prefetch_isrc_data(chosen_matches)
            for source_track, match in pairs_to_embed:
                self._update_spotify_match_in_source_track(source_track, match)

        return sp_tracks
