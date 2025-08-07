import os
from dotenv import load_dotenv


load_dotenv()


class AppSettings:
    """
    settings module for ARS
    """

    @property
    def db_url(self):
        db_path = "/home/ars.db"
        return f"sqlite+aiosqlite:///{db_path}"

    @property
    def SMTP_ENV_KEY(self):
        return os.getenv("SMTP_ENV_KEY")


settings = AppSettings()
