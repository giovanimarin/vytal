from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    google_client_id: str = Field(..., env="GOOGLE_CLIENT_ID")
    google_client_secret: str = Field(..., env="GOOGLE_CLIENT_SECRET")
    google_redirect_uri: str = Field(
        "http://localhost:8000/api/v1/connect/google_fit/callback",
        env="GOOGLE_REDIRECT_URI",
    )
    secret_key: str = Field("dev-secret-change-in-prod", env="SECRET_KEY")
    environment: str = Field("local", env="ENVIRONMENT")
    config_path: str = Field("./config.yaml", env="CONFIG_PATH")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
