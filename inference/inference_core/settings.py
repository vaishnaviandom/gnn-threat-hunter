"""
inference/inference_core/settings.py

Django settings for the GNN Inference Microservice (Phase 9).

This is a lightweight, stateless Django service. It:
 - Receives subgraph batches from the Django backend orchestrator
 - Runs ONNX + CoreML inference using Apple Silicon MPS/Neural Engine
 - Returns anomaly scores back to the orchestrator
 - Uses async Django views for dynamic batching (replaces Triton)

Runs on port 8001 (backend runs on 8000).
"""

import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR.parent / ".env")

SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY", "inference-insecure-CHANGE-ME")
DEBUG = os.environ.get("DJANGO_DEBUG", "True") == "True"
ALLOWED_HOSTS = os.environ.get("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1").split(",")

INSTALLED_APPS = [
    "django.contrib.contenttypes",
    "django.contrib.auth",
    "rest_framework",
    "scoring",    # Phase 9: ONNX scoring app
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.middleware.common.CommonMiddleware",
]

ROOT_URLCONF = "inference_core.urls"
ASGI_APPLICATION = "inference_core.asgi.application"

# No database needed — stateless scoring service
DATABASES = {}

REST_FRAMEWORK = {
    "DEFAULT_RENDERER_CLASSES": ["rest_framework.renderers.JSONRenderer"],
    "DEFAULT_PERMISSION_CLASSES": ["rest_framework.permissions.AllowAny"],
}

# ── Inference model paths (Phase 9) ──────────────────────────────────────────
INFERENCE = {
    "MODEL_PATH_ONNX": os.environ.get("MODEL_PATH_ONNX", str(BASE_DIR / "models" / "gnn_model.onnx")),
    "MODEL_PATH_MLPACKAGE": os.environ.get("MODEL_PATH_MLPACKAGE", str(BASE_DIR / "models" / "gnn_model.mlpackage")),
    "BATCH_MAX": int(os.environ.get("INFERENCE_BATCH_MAX", "32")),
    "BATCH_TIMEOUT_MS": int(os.environ.get("INFERENCE_BATCH_TIMEOUT_MS", "50")),
    "ANOMALY_THRESHOLD": float(os.environ.get("ANOMALY_THRESHOLD", "0.75")),
}

LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_TZ = True
