import configparser
import os
import shutil

HERE = os.path.abspath(os.path.dirname(__file__))
CONFIG_PATH = os.path.join(HERE, "config.ini")
CONFIG_TEMPLATE_PATH = os.path.join(HERE, "config_template.ini")

if not os.path.exists(CONFIG_PATH):
    shutil.copyfile(CONFIG_TEMPLATE_PATH, CONFIG_PATH)


class Config:
    def __init__(self):
        self.config = configparser.ConfigParser()
        self.config.read(CONFIG_PATH)

    @property
    def spotify_client_id(self):
        return self.config.get("SPOTIFY", "CLIENT_ID")

    @property
    def spotify_client_secret(self):
        return self.config.get("SPOTIFY", "CLIENT_SECRET")

    @property
    def spotify_redirect_url(self):
        return self.config.get("SPOTIFY", "REDIRECT_URL")

    # Deezer configuration accessors
    @property
    def deezer_access_token(self):
        # Returns None if not set
        return self.config.get("DEEZER", "ACCESS_TOKEN", fallback=None)

    @property
    def deezer_app_id(self):
        return self.config.get("DEEZER", "APP_ID", fallback=None)

    @property
    def deezer_app_secret(self):
        return self.config.get("DEEZER", "APP_SECRET", fallback=None)

    @property
    def deezer_redirect_url(self):
        return self.config.get("DEEZER", "REDIRECT_URL", fallback=None)


CONFIG = Config()
