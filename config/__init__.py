import configparser
import os
import shutil

CONFIG_PATH = os.path.join("config", "config.ini")
CONFIG_TEMPLATE_PATH = os.path.join("config", "config_template.ini")

if not os.path.exists(CONFIG_PATH):
    shutil.copyfile(CONFIG_TEMPLATE_PATH, CONFIG_PATH)


class Config:
    def __init__(self):
        self.config = configparser.ConfigParser()
        self.config.read('config/config.ini')

    @property
    def spotify_client_id(self):
        return self.config.get("SPOTIFY", "CLIENT_ID")

    @property
    def spotify_client_secret(self):
        return self.config.get("SPOTIFY", "CLIENT_SECRET")

    @property
    def spotify_redirect_url(self):
        return self.config.get("SPOTIFY", "REDIRECT_URL")


CONFIG = Config()
