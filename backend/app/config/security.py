"""Pure configuration policy. Errors identify fields, never their values."""
from ipaddress import ip_address
from urllib.parse import urlsplit


class ConfigurationError(ValueError):
    """An unsafe or incomplete runtime configuration."""


_LOCAL = {"local", "dev", "development", "test", "testing"}
_ENVIRONMENTS = _LOCAL | {"production", "prod", "staging"}
_UNSAFE = {
    "dev-secret-change-in-prod", "dev-secret-change-in-production", "change-me", "changeme",
    "your-secret", "your-client-secret", "test-secret-key", "test-client-secret", "secret",
    "password", "synthetic", "synthetic-ci", "demo1234",
}


def environment_name(value: str | None) -> str:
    if not isinstance(value, str) or value.strip().lower() not in _ENVIRONMENTS:
        raise ConfigurationError("ENVIRONMENT must be explicitly set to a supported environment")
    return value.strip().lower()


def is_local(value: str) -> bool:
    return environment_name(value) in _LOCAL


def require_secret(value: str | None, field: str, *, production: bool) -> None:
    if not isinstance(value, str) or not value.strip():
        raise ConfigurationError(f"{field} must be explicitly configured")
    if production and (value.strip().lower() in _UNSAFE or value.lower().startswith(("your-", "replace-", "dev-secret"))):
        raise ConfigurationError(f"{field} contains an unsafe placeholder")


def require_https(value: str, field: str, *, origin: bool = False) -> None:
    try:
        parsed = urlsplit(value)
        hostname = parsed.hostname
        _ = parsed.port  # Validate malformed ports without including their input in errors.
        loopback = hostname in {"localhost", "localhost.localdomain"} or bool(hostname and hostname.endswith(".localhost"))
        try:
            address = ip_address(hostname or "")
            mapped = getattr(address, "ipv4_mapped", None)
            loopback = loopback or address.is_loopback or address.is_unspecified
            loopback = loopback or bool(mapped and (mapped.is_loopback or mapped.is_unspecified))
        except ValueError:
            pass
        valid = parsed.scheme == "https" and hostname and "*" not in hostname and not loopback
        valid = valid and not parsed.username and not parsed.password and not parsed.fragment
        if origin:
            valid = valid and parsed.path in {"", "/"} and not parsed.query
        if not valid:
            raise ValueError
    except (ValueError, TypeError):
        raise ConfigurationError(f"{field} must be an explicit HTTPS URL without local host or credentials") from None
