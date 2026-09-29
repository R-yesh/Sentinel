from pydantic_settings import BaseSettings
from pydantic import Field, field_validator
from urllib.parse import urlsplit


class Settings(BaseSettings):
    app_name: str = "Sentinel API"
    app_version: str = "0.1.0"
    environment: str = "development"
    sentinel_cors_origins: list[str] = Field(default_factory=list)

    @field_validator('sentinel_cors_origins')
    @classmethod
    def exact_origins(cls, values):
        origins = []
        for value in values:
            parsed = urlsplit(value)
            if (parsed.scheme not in ('http', 'https') or not parsed.hostname
                    or '*' in value or parsed.username or parsed.password
                    or parsed.path not in ('', '/') or parsed.query or parsed.fragment):
                raise ValueError('CORS entries must be exact HTTP(S) origins without wildcards or paths.')
            origins.append(value.rstrip('/'))
        return origins


settings = Settings()
