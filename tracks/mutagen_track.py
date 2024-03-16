from typing import List

import mutagen

from tracks.track import Track


class MutagenTrack(Track):
    def __init__(self, file_path: str):
        self._audio = mutagen.File(file_path)

    @property
    def artists(self) -> List[str]:
        return self._get_tag("artist")

    @property
    def title(self) -> str:
        return self._get_tag("title")[0]

    @property
    def album(self) -> str:
        return self._get_tag("album")[0]

    @property
    def duration(self) -> int:
        return self._audio.info.length

    def _get_tag(self, tag_name, assert_not_empty=True):
        result = self._audio.get(tag_name)
        if assert_not_empty and not result:
            raise AttributeError(f"No {tag_name} found")
        return result
