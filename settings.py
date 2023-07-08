from pydantic import BaseSettings, PostgresDsn


class Settings(BaseSettings):
    database: PostgresDsn
    secret: str
    port: int
    root_path: str


settings = Settings()
