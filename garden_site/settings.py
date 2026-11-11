"""Settings for the garden plot registry."""
import importlib.util
import os
import sys
from pathlib import Path
from urllib.parse import parse_qs, unquote, urlparse

BASE_DIR = Path(__file__).resolve().parent.parent
# The manifest static storage needs collectstatic output, which tests do not build.
TESTING = "pytest" in sys.modules or "test" in sys.argv
SECRET_KEY = os.getenv("DJANGO_SECRET_KEY", "local-only-change-me")
DEBUG = os.getenv("DJANGO_DEBUG", "0") == "1"
ALLOWED_HOSTS = [host.strip() for host in os.getenv("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1").split(",") if host.strip()]
RENDER_HOSTNAME = os.getenv("RENDER_EXTERNAL_HOSTNAME", "").strip()
if RENDER_HOSTNAME and RENDER_HOSTNAME not in ALLOWED_HOSTS:
    ALLOWED_HOSTS.append(RENDER_HOSTNAME)
CSRF_TRUSTED_ORIGINS = [origin.strip() for origin in os.getenv("DJANGO_CSRF_TRUSTED_ORIGINS", "").split(",") if origin.strip()]
if RENDER_HOSTNAME:
    CSRF_TRUSTED_ORIGINS.append(f"https://{RENDER_HOSTNAME}")

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "home.apps.HomeConfig",
    "registry.apps.RegistryConfig",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

# Django Debug Toolbar analyses SQL only in the development mode (PR10, 5.4.1).
if DEBUG and importlib.util.find_spec("debug_toolbar"):
    INSTALLED_APPS.append("debug_toolbar")
    MIDDLEWARE.insert(0, "debug_toolbar.middleware.DebugToolbarMiddleware")
    INTERNAL_IPS = ["127.0.0.1", "localhost"]

ROOT_URLCONF = "garden_site.urls"
TEMPLATES = [{
    "BACKEND": "django.template.backends.django.DjangoTemplates",
    "DIRS": [BASE_DIR / "templates"],
    "APP_DIRS": True,
    "OPTIONS": {"context_processors": [
        "django.template.context_processors.request",
        "django.contrib.auth.context_processors.auth",
        "django.contrib.messages.context_processors.messages",
        "registry.context_processors.registry_summary",
    ]},
}]
WSGI_APPLICATION = "garden_site.wsgi.application"


def database_config():
    """Read a provider URL, tolerating a pasted `psql '…'` command."""
    url = os.getenv("DATABASE_URL", "").strip()
    if not url:
        return {"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": BASE_DIR / "data" / "garden.sqlite3"}}
    if url.lower().startswith("psql "):
        url = url[5:].strip()
    url = url.strip("'\"").strip()
    if url.startswith("postgresql+psycopg://"):
        url = url.replace("postgresql+psycopg://", "postgresql://", 1)
    parsed = urlparse(url)
    # Render and several PostgreSQL providers still issue the legacy postgres:// form.
    if parsed.scheme in {"postgres", "postgresql"}:
        query_options = parse_qs(parsed.query)
        options = {"sslmode": query_options.get("sslmode", ["require"])[0]}
        if "channel_binding" in query_options:
            options["channel_binding"] = query_options["channel_binding"][0]
        return {"default": {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": unquote(parsed.path.lstrip("/")),
            "USER": unquote(parsed.username or ""),
            "PASSWORD": unquote(parsed.password or ""),
            "HOST": parsed.hostname or "",
            "PORT": parsed.port or 5432,
            "OPTIONS": options,
            "CONN_MAX_AGE": 60,
        }}
    if parsed.scheme == "sqlite":
        name = unquote(parsed.path)
        return {"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": name or BASE_DIR / "data" / "garden.sqlite3"}}
    raise ValueError("DATABASE_URL must use postgres://, postgresql://, or sqlite://")


DATABASES = database_config()
LANGUAGE_CODE = "ru"
TIME_ZONE = "Europe/Moscow"
USE_I18N = True
USE_TZ = True
STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [BASE_DIR / "static"]
# Uploaded plot images (PR11, subsection 5.6).
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"
# Files above the form limit are rejected before they reach the model.
FILE_UPLOAD_MAX_MEMORY_SIZE = 5 * 1024 * 1024
STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {
        "BACKEND": (
            "django.contrib.staticfiles.storage.StaticFilesStorage"
            if DEBUG or TESTING
            else "whitenoise.storage.CompressedManifestStaticFilesStorage"
        ),
    },
}
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
