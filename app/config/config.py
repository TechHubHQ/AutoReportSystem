class AppSettings:
    """
    settings module for ARS
    """

    @property
    def db_url():
        return "sqlite3:///ars.db"


settings = AppSettings()