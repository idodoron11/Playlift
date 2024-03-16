from typing import List

import music_tag

from tracks import Track


class LocalTrack(Track):
    def __init__(self, file_path: str):
        self._audio = music_tag.load_file(file_path)

    @property
    def artists(self) -> List[str]:
        return self._get_tag("artist").values

    @property
    def display_artist(self) -> str:
        return self._get_tag("artist").value

    @property
    def title(self) -> str:
        return self._get_tag("title").first

    @property
    def album(self) -> str:
        return self._get_tag("album").first

    @property
    def duration(self) -> float:
        return self._get_tag("#length").first

    def _get_tag(self, tag_name, assert_not_empty=True):
        result = self._audio[tag_name]
        if assert_not_empty and not result:
            raise AttributeError(f"No {tag_name} found")
        return result
