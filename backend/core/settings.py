"""
Django settings for GNN Threat Hunter — Backend Core.

Phase 0 configuration: PostgreSQL, DRF, env-driven secrets.
Extended progressively through Phase 5 (Memgraph), Phase 9 (ONNX),
and Phase 13 (production hardening).
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# ── Load .env from repo root ──────────────────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR.parent / ".env")

# ── Security ──────────────────────────────────────────────────────────────────
SECRET_KEY = os.environ.get(
    "DJANGO_SECRET_KEY",
    "django-insecure-CHANGE-ME-BEFORE-PRODUCTION",
)
DEBUG = os.environ.get("DJANGO_DEBUG", "True") == "True"
ALLOWED_HOSTS = os.environ.get("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1").split(",")

# ── Applications ──────────────────────────────────────────────────────────────
INSTALLED_APPS = [
    # Django defaults
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # Third party
    "rest_framework",
    # Local — Phase 0 apps
    "telemetry_api",   # Receives OCSF events from the ESF daemon (Phase 1)
    "graph_api",       # Exposes Memgraph query endpoints (Phase 4)
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "core.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "core.wsgi.application"
ASGI_APPLICATION = "core.asgi.application"  # Phase 9: Django Channels

# ── Database (PostgreSQL) ─────────────────────────────────────────────────────
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.environ.get("POSTGRES_DB", "gnn_threatdb"),
        "USER": os.environ.get("POSTGRES_USER", "gnn_user"),
        "PASSWORD": os.environ.get("POSTGRES_PASSWORD", "change_me_now"),
        "HOST": os.environ.get("POSTGRES_HOST", "localhost"),
        "PORT": os.environ.get("POSTGRES_PORT", "5432"),
    }
}

# ── Django REST Framework ─────────────────────────────────────────────────────
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework.authentication.SessionAuthentication",
        "rest_framework.authentication.BasicAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
    "DEFAULT_RENDERER_CLASSES": [
        "rest_framework.renderers.JSONRenderer",
    ],
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 50,
}

# ── Memgraph connection settings (Phase 4) ────────────────────────────────────
MEMGRAPH = {
    "HOST": os.environ.get("MEMGRAPH_HOST", "localhost"),
    "PORT": int(os.environ.get("MEMGRAPH_PORT", "7687")),
    "USERNAME": os.environ.get("MEMGRAPH_USERNAME", ""),
    "PASSWORD": os.environ.get("MEMGRAPH_PASSWORD", ""),
}

# ── Inference service settings (Phase 9) ─────────────────────────────────────
INFERENCE = {
    "SERVICE_URL": os.environ.get("INFERENCE_SERVICE_URL", "http://localhost:8001"),
    "BATCH_MAX": int(os.environ.get("INFERENCE_BATCH_MAX", "32")),
    "BATCH_TIMEOUT_MS": int(os.environ.get("INFERENCE_BATCH_TIMEOUT_MS", "50")),
}

# ── Internationalization ───────────────────────────────────────────────────────
LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

# ── Static files ──────────────────────────────────────────────────────────────
STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
