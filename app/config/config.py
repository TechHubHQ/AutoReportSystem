import os
from dotenv import load_dotenv

load_dotenv()


class AppSettings:
    """
    Settings module for ARS (App Reporting System)
    """

    @property
    def db_url(self):
        return os.getenv("DB_URL")

    @property
    def SMTP_ENV_KEY(self):
        return os.getenv("SMTP_ENV_KEY")


# Instantiate settings
settings = AppSettings()
