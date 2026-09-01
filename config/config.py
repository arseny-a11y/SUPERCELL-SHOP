from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    DB_NAME: str = 'app/database/database.db'
    TOKEN: str
    PROXY_URL: str

    @property
    def DATABASE_URL_aiosqlite(self) -> str:
        return f'sqlite+aiosqlite:///{self.DB_NAME}'

    @property
    def DATABASE_URL_sqlite(self) -> str:
        return f'sqlite:///{self.DB_NAME}'

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()