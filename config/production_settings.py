"""Compatibility for older deployment commands; APP_ENV still selects the file."""
from .settings import *  # noqa: F401,F403
from django.core.exceptions import ImproperlyConfigured

if APP_ENV != "production":
    raise ImproperlyConfigured("Set APP_ENV=production before using config.production_settings.")
