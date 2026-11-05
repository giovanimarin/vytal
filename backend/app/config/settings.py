import os
import secrets

from pydantic import Field, SecretStr, ValidationError, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict, SettingsError

from app.config.security import (
    ConfigurationError,
    environment_name,
    is_local,
    require_https,
    require_secret,
)


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=None, extra="ignore", hide_input_in_errors=True)

    environment: str
    google_client_id: str
    google_client_secret: SecretStr
    google_redirect_uri: str | None = None
    secret_key: SecretStr | None = None
    jwt_secret_key: SecretStr | None = None
    config_path: str | None = None
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = Field(60, gt=0)
    refresh_token_expire_days: int = Field(7, gt=0)
    cors_origins: list[str] = Field(default_factory=list)
    allow_dev_seed: bool = False
    demo_email: str = "demo@example.invalid"
    demo_password: SecretStr | None = None

    @model_validator(mode="after")
    def validate_security(self):
        self.environment = environment_name(self.environment)
        local = is_local(self.environment)
        for field in ("secret_key", "jwt_secret_key"):
            value = getattr(self, field)
            if value is None and local:
                setattr(self, field, SecretStr(secrets.token_urlsafe(48)))
            else:
                require_secret(value.get_secret_value() if value is not None else None,
                               field.upper(), production=not local)
        require_secret(self.google_client_secret.get_secret_value(), "GOOGLE_CLIENT_SECRET", production=not local)
        if not self.google_client_id.strip():
            raise ConfigurationError("GOOGLE_CLIENT_ID must be explicitly configured")
        if self.jwt_algorithm != "HS256":
            raise ConfigurationError("JWT_ALGORITHM must use the supported HS256 algorithm")
        if self.google_redirect_uri is None and local:
            self.google_redirect_uri = "http://localhost:8000/api/v1/connect/google_fit/callback"
        if self.config_path is None and local:
            self.config_path = "./config.yaml"
        if not self.config_path or not self.config_path.strip():
            raise ConfigurationError("CONFIG_PATH must be explicitly configured")
        if not local:
            require_https(self.google_redirect_uri or "", "GOOGLE_REDIRECT_URI")
            for value in self.cors_origins:
                require_https(value, "CORS_ORIGINS", origin=True)
            if self.allow_dev_seed or self.demo_password is not None:
                raise ConfigurationError("Development seed configuration is not permitted outside local/test")
        if self.allow_dev_seed:
            value = self.demo_password.get_secret_value() if self.demo_password is not None else None
            require_secret(value, "DEMO_PASSWORD", production=True)
            if len(value) < 8:
                raise ConfigurationError("DEMO_PASSWORD must meet the existing registration policy")
            if not self.demo_email.strip():
                raise ConfigurationError("DEMO_EMAIL must be configured for development seed")
        return self


def load_settings() -> Settings:
    # A copied development .env must never decide the deployment environment.
    environment = environment_name(os.environ.get("ENVIRONMENT"))
    if is_local(environment) and os.environ.get("K_SERVICE"):
        raise ConfigurationError("ENVIRONMENT must use production/staging on a managed service")
    try:
        return Settings(environment=environment, _env_file=".env" if environment in {"local", "dev", "development"} else None)
    except ValidationError as error:
        fields = set()
        for item in error.errors(include_input=False, include_context=False):
            if item["loc"]:
                fields.add(str(item["loc"][0]).upper())
            else:
                fields.update(name.upper() for name in Settings.model_fields if name.upper() in item["msg"])
        fields = sorted(fields)
        detail = ", ".join(fields) if fields else "security policy"
        raise ConfigurationError(f"Invalid configuration: {detail}") from None
    except SettingsError:
        raise ConfigurationError("Invalid environment configuration encoding") from None


settings = load_settings()


def get_settings() -> Settings:
    return settings
