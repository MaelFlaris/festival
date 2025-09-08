"""
Django settings for festival_backend project (V2 ready).
"""
import os
from pathlib import Path

# ---------------------------------------------------------------------
# Bases
# ---------------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent.parent
COMMON_WEBHOOK_URLS = [
    u.strip() for u in os.getenv("COMMON_WEBHOOK_URLS", "").split(",") if u.strip()
]
COMMON_WEBHOOK_SECRET = os.getenv("COMMON_WEBHOOK_SECRET") 
def env_bool(key: str, default: bool) -> bool:
    return str(os.getenv(key, str(default))).lower() in ("1", "true", "yes", "on")

# IMPORTANT: en prod, surcharger par variable d'env
SECRET_KEY = 'django-insecure-i1@ns5gilmiyrz9_st(bz3qy05rp4$79=#5d$oe66-+1u716#q'
DEBUG = env_bool("DEBUG", True)

ALLOWED_HOSTS = (
    [h.strip() for h in os.getenv("ALLOWED_HOSTS", "").split(",") if h.strip()]
    if not DEBUG else ["*"]
)

# ---------------------------------------------------------------------
# CORS
# ---------------------------------------------------------------------
CORS_ALLOW_ALL_ORIGINS = env_bool("CORS_ALLOW_ALL_ORIGINS", DEBUG)
CORS_ALLOWED_ORIGINS = [
    o.strip() for o in os.getenv("CORS_ALLOWED_ORIGINS", "").split(",") if o.strip()
] if not CORS_ALLOW_ALL_ORIGINS else []
CORS_ALLOW_CREDENTIALS = True

# ---------------------------------------------------------------------
# I18N / TZ
# ---------------------------------------------------------------------
LANGUAGE_CODE = "fr-fr"
TIME_ZONE = "Europe/Paris"
USE_TZ = True

# ---------------------------------------------------------------------
# Applications
# ---------------------------------------------------------------------
INSTALLED_APPS = [
    # tiers
    "corsheaders",
    "rest_framework",
    "django_filters",
    "guardian",

    # apps projet
    "apps.common",
    "apps.core",
    "apps.lineup",
    "apps.schedule",
    "apps.sponsors",
    "apps.tickets",
    "apps.cms",
    "apps.authx",

    # django
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
]

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "festival_backend.urls"

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

WSGI_APPLICATION = "festival_backend.wsgi.application"
ASGI_APPLICATION = "festival_backend.asgi.application"

# ---------------------------------------------------------------------
# Auth redirects (browsable API UX)
# ---------------------------------------------------------------------
LOGIN_REDIRECT_URL = "/api/v1/"
LOGOUT_REDIRECT_URL = "/api/v1/"

# ---------------------------------------------------------------------
# DB
# ---------------------------------------------------------------------
# Utilise PostgreSQL si les variables d'environnement nécessaires sont définies,
# sinon bascule sur une base SQLite locale (pratique pour les tests).
POSTGRES_HOST = os.getenv("POSTGRES_HOST")
if POSTGRES_HOST:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": os.getenv("POSTGRES_DB", "festival"),
            "USER": os.getenv("POSTGRES_USER", "festival"),
            "PASSWORD": os.getenv("POSTGRES_PASSWORD", "changeme"),
            "HOST": POSTGRES_HOST,
            "PORT": os.getenv("POSTGRES_PORT", "5432"),
        }
    }
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }

# ---------------------------------------------------------------------
# Cache (Redis si REDIS_URL, sinon mémoire locale)
# ---------------------------------------------------------------------
REDIS_URL = os.getenv("REDIS_URL", "").strip()
if REDIS_URL:
    CACHES = {
        "default": {
            "BACKEND": "django.core.cache.backends.redis.RedisCache",
            "LOCATION": REDIS_URL,
        }
    }
else:
    CACHES = {
        "default": {
            "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
            "LOCATION": "festival-cache",
        }
    }

# ---------------------------------------------------------------------
# DRF
# ---------------------------------------------------------------------
REST_FRAMEWORK = {
    "DEFAULT_FILTER_BACKENDS": [
        "django_filters.rest_framework.DjangoFilterBackend",
        "rest_framework.filters.SearchFilter",
        "rest_framework.filters.OrderingFilter",
    ],
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework.authentication.SessionAuthentication",
        "rest_framework.authentication.BasicAuthentication",
    ],
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": int(os.getenv("DRF_PAGE_SIZE", "50")),
    # throttles génériques (les réservations tickets ont déjà un RL interne)
    "DEFAULT_THROTTLE_CLASSES": [
        "rest_framework.throttling.AnonRateThrottle",
        "rest_framework.throttling.UserRateThrottle",
    ],
    "DEFAULT_THROTTLE_RATES": {
        "anon": os.getenv("DRF_THROTTLE_ANON", "200/min"),
        "user": os.getenv("DRF_THROTTLE_USER", "1000/min"),
    },
}

# ---------------------------------------------------------------------
# Auth
# ---------------------------------------------------------------------
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# ---------------------------------------------------------------------
# Static
# ---------------------------------------------------------------------
STATIC_URL = "static/"
STATIC_ROOT = os.getenv("STATIC_ROOT", str(BASE_DIR / "staticfiles"))

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# ---------------------------------------------------------------------
# Sécurité (prod : à ajuster)
# ---------------------------------------------------------------------
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https") if env_bool("SECURE_BEHIND_PROXY", False) else None
CSRF_TRUSTED_ORIGINS = [
    o.strip() for o in os.getenv("CSRF_TRUSTED_ORIGINS", "").split(",") if o.strip()
]

# ---------------------------------------------------------------------
# App settings (TTL, rate limit, S3 sponsors)
# ---------------------------------------------------------------------
SCHEDULE_LIST_DAY_CACHE_TTL = int(os.getenv("SCHEDULE_LIST_DAY_CACHE_TTL", "120"))
SCHEDULE_ICS_CACHE_TTL = int(os.getenv("SCHEDULE_ICS_CACHE_TTL", "120"))
SPONSORS_PUBLIC_CACHE_TTL = int(os.getenv("SPONSORS_PUBLIC_CACHE_TTL", "300"))
TICKETS_ON_SALE_CACHE_TTL = int(os.getenv("TICKETS_ON_SALE_CACHE_TTL", "120"))
TICKETS_RESERVE_RATE_LIMIT_PER_MIN = int(os.getenv("TICKETS_RESERVE_RATE_LIMIT_PER_MIN", "30"))
COMMON_WEBHOOK_TIMEOUT = int(os.getenv("COMMON_WEBHOOK_TIMEOUT", "5"))

# S3 pour sponsors (facultatif)
SPONSORS_S3_BUCKET = os.getenv("SPONSORS_S3_BUCKET")
SPONSORS_S3_REGION = os.getenv("SPONSORS_S3_REGION")
SPONSORS_S3_PREFIX = os.getenv("SPONSORS_S3_PREFIX", "contracts/")

# ---------------------------------------------------------------------
# Logging minimal
# ---------------------------------------------------------------------
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "simple": {"format": "%(levelname)s %(name)s: %(message)s"},
    },
    "handlers": {
        "console": {"class": "logging.StreamHandler", "formatter": "simple"},
    },
    "root": {"handlers": ["console"], "level": LOG_LEVEL},
}

# ---------------------------------------------------------------------
# Guardian RBAC (object-level permissions)
# ---------------------------------------------------------------------
AUTHENTICATION_BACKENDS = [
    "django.contrib.auth.backends.ModelBackend",
    "guardian.backends.ObjectPermissionBackend",
]
GUARDIAN_ANONYMOUS_USER_NAME = None
LOGIN_REDIRECT_URL = "/api/v1/"   
LOGOUT_REDIRECT_URL = "/api/v1/" 
