import os
from dotenv import load_dotenv

load_dotenv()


class AppSettings:
    """
    Settings module for ARS (App Reporting System)
    """

    @property
    def db_url(self):
        # Use a safe writable directory inside the project folder
        db_dir = ".streamlit"
        os.makedirs(db_dir, exist_ok=True)  # Ensure the directory exists

        db_path = os.path.join(db_dir, "ars.db")
        return f"sqlite+aiosqlite:///{db_path}"

    @property
    def SMTP_ENV_KEY(self):
        return os.getenv("SMTP_ENV_KEY")


# Instantiate settings
settings = AppSettings()
