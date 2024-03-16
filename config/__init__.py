import configparser
import os
import shutil

if not os.path.exists('config/config.ini'):
    shutil.copyfile("config/config_template.ini", "config/config.ini")


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
