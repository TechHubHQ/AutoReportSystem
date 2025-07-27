import os
from dotenv import load_dotenv


load_dotenv()


class AppSettings:
    """
    settings module for ARS
    """

    @property
    def db_url(self):
        return "sqlite+aiosqlite:///ars.db"

    @property
    def SMTP_ENV_KEY(self):
        return os.getenv("SMTP_ENV_KEY")


settings = AppSettings()
