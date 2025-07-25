class AppSettings:
    """
    settings module for ARS
    """

    @property
    def db_url(self):
        return "sqlite+aiosqlite:///ars.db" 


settings = AppSettings()