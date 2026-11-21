from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Pixel Unicorn"
    database_url: str = "sqlite:///./pixel_unicorn.db"
    # Required, no default: a guessable key lets anyone forge JWTs.
    # Generate one with: python -c "import secrets; print(secrets.token_hex(32))"
    secret_key: str = Field(min_length=32)
    access_token_expire_minutes: int = 60
    jwt_algorithm: str = "HS256"
    model_config = SettingsConfigDict(env_file=".env")


settings = Settings()
