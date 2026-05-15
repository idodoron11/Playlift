import configparser
import shutil
from pathlib import Path

_HERE = Path(__file__).parent
CONFIG_TEMPLATE_PATH = _HERE / "config_template.ini"

CONFIG_DIR = Path.home() / ".playlift"
CONFIG_PATH = CONFIG_DIR / "config.ini"

if not CONFIG_PATH.exists():
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(CONFIG_TEMPLATE_PATH, CONFIG_PATH)


class Config:
    def __init__(self) -> None:
        self.config = configparser.ConfigParser()
        self.config.read(CONFIG_PATH)  # Path objects accepted since Python 3.4

    @property
    def spotify_client_id(self) -> str:
        return self.config.get("SPOTIFY", "CLIENT_ID")

    @property
    def spotify_client_secret(self) -> str:
        return self.config.get("SPOTIFY", "CLIENT_SECRET")

    @property
    def spotify_redirect_url(self) -> str:
        return self.config.get("SPOTIFY", "REDIRECT_URL")

    @property
    def deezer_arl(self) -> str:
        return self.config.get("DEEZER", "ARL")


CONFIG = Config()
