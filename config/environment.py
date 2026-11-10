"""Select one environment file before Django settings are evaluated."""
import os
from dataclasses import dataclass
from pathlib import Path

from django.core.exceptions import ImproperlyConfigured
from dotenv import dotenv_values, load_dotenv


@dataclass(frozen=True)
class Environment:
    name: str
    path: Path | None


def load_environment(base_dir):
    name = os.environ.get("APP_ENV", "development").strip().lower()
    if name not in {"development", "testing", "production"}:
        raise ImproperlyConfigured("APP_ENV must be development, testing or production.")
    explicit = os.environ.get("DJANGO_ENV_FILE")
    path = Path(explicit) if explicit else Path(f".env.{name}")
    if not path.is_absolute():
        path = Path(base_dir) / path
    if not explicit and name == "development" and not path.is_file():
        path = Path(base_dir) / ".env"
    if not path.is_file():
        if explicit or name != "development":
            raise ImproperlyConfigured(f"Environment file does not exist: {path}")
        return Environment(name, None)
    selector = dotenv_values(path, encoding="utf-8-sig", interpolate=False).get("APP_ENV")
    if selector and selector.strip().lower() != name:
        raise ImproperlyConfigured("Set APP_ENV in the process, not in a different environment file.")
    os.environ.setdefault("APP_ENV", name)
    load_dotenv(path, override=False, encoding="utf-8-sig")
    return Environment(name, path)


def apply_deployment_settings(namespace, name):
    if name == "testing" and not os.environ.get("DB_NAME", "").strip():
        raise ImproperlyConfigured("Testing requires an explicit DB_NAME for its separate database.")
    if name == "production":
        hosts = [value.strip() for value in os.environ.get("DJANGO_ALLOWED_HOSTS", "").split(",") if value.strip()]
        if not hosts or "*" in hosts:
            raise ImproperlyConfigured("Production requires explicit DJANGO_ALLOWED_HOSTS without *.")
        secret = os.environ.get("DJANGO_SECRET_KEY", "")
        if len(secret) < 32 or secret.lower().startswith(("replace", "change", "django-insecure", "dev-only")):
            raise ImproperlyConfigured("Production requires a new DJANGO_SECRET_KEY of at least 32 characters.")
        for key in ("DB_NAME", "DB_USER", "DB_HOST", "DB_PORT"):
            if not os.environ.get(key, "").strip():
                raise ImproperlyConfigured(f"Production requires an explicit {key}.")
        namespace.update(DEBUG=False, ALLOWED_HOSTS=hosts)
    https = os.environ.get("DJANGO_HTTPS", "1" if name == "production" else "0") == "1"
    namespace.update(
        CSRF_TRUSTED_ORIGINS=[value.strip() for value in os.environ.get("DJANGO_CSRF_TRUSTED_ORIGINS", "").split(",") if value.strip()],
        SECURE_PROXY_SSL_HEADER=("HTTP_X_FORWARDED_PROTO", "https"),
        SECURE_SSL_REDIRECT=https,
        SESSION_COOKIE_SECURE=https,
        CSRF_COOKIE_SECURE=https,
        LANGUAGE_COOKIE_SECURE=https,
        SECURE_HSTS_SECONDS=int(os.environ.get("DJANGO_HSTS_SECONDS", "0")),
        SECURE_CONTENT_TYPE_NOSNIFF=True,
    )
