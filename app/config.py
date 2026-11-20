from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Pixel Unicorn"
    database_url: str = "sqlite:///./pixel_unicorn.db"
    secret_key: str = "change-me"
    access_token_expire_minutes: int = 60

    model_config = SettingsConfigDict(env_file=".env")


settings = Settings()