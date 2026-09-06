from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "Sentinel API"
    app_version: str = "0.1.0"
    environment: str = "development"


settings = Settings()