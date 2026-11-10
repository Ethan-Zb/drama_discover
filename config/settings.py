from pathlib import Path
import os
from .environment import load_environment, apply_deployment_settings

BASE_DIR = Path(__file__).resolve().parent.parent

_environment = load_environment(BASE_DIR)
APP_ENV = _environment.name
ENV_FILE = _environment.path

SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY", "dev-only-change-this-secret-key")
DEBUG = os.environ.get("DJANGO_DEBUG", "1" if APP_ENV == "development" else "0") == "1"
ALLOWED_HOSTS = [h.strip() for h in os.environ.get("DJANGO_ALLOWED_HOSTS", "127.0.0.1,localhost").split(",") if h.strip()]

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "core",
    "drama",
    "advertising",
    "analytics",
    "platforms",
    "operations",
]

CMS_LOCAL_HOSTS = [h.strip() for h in os.environ.get("CMS_LOCAL_HOSTS", "127.0.0.1,localhost,testserver").split(",") if h.strip()]
# SiteMiddleware validates the exact host against active registered sites.
ALLOWED_HOSTS = ["*"]
LOGIN_URL = "/cms/login/"
LOGIN_REDIRECT_URL = "/cms/"
LOGOUT_REDIRECT_URL = "/cms/login/"

MIDDLEWARE = [
    "operations.middleware.SiteMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.locale.LocaleMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [{
    "BACKEND": "django.template.backends.django.DjangoTemplates",
    "DIRS": [BASE_DIR / "templates"],
    "APP_DIRS": True,
    "OPTIONS": {
        "context_processors": [
            "django.template.context_processors.debug",
            "django.template.context_processors.request",
            "django.contrib.auth.context_processors.auth",
            "django.contrib.messages.context_processors.messages",
            "core.context_processors.site_settings",
        ],
    },
}]

WSGI_APPLICATION = "config.wsgi.application"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.mysql",
        "NAME": os.environ.get("DB_NAME", "short_drama_db"),
        "USER": os.environ.get("DB_USER", "root"),
        "PASSWORD": os.environ.get("DB_PASSWORD", ""),
        "HOST": os.environ.get("DB_HOST", "127.0.0.1"),
        "PORT": os.environ.get("DB_PORT", "3306"),
        "OPTIONS": {"charset": "utf8mb4"},
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "zh-hans"
LANGUAGES = [("zh-hans", "简体中文"), ("en", "English")]
LOCALE_PATHS = [BASE_DIR / "locale"]
LANGUAGE_COOKIE_AGE = 365 * 24 * 60 * 60
LANGUAGE_COOKIE_SAMESITE = "Lax"
TIME_ZONE = "Asia/Shanghai"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"
MEDIA_URL = "media/"
MEDIA_ROOT = BASE_DIR / "media"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Development default. Configure secure cookies/HTTPS before production deployment.
X_FRAME_OPTIONS = "SAMEORIGIN"

apply_deployment_settings(globals(), APP_ENV)
