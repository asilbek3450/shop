import os
from pathlib import Path

import dj_database_url
from dotenv import load_dotenv


BASE_DIR = Path(__file__).resolve().parent.parent

load_dotenv(BASE_DIR / ".env")


def env(name, default=None):
    return os.getenv(name, default)


def env_bool(name, default=False):
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.lower() in {"1", "true", "yes", "on"}


SECRET_KEY = env("DJANGO_SECRET_KEY", "django-insecure-dev-key-change-me")
DEBUG = env_bool("DJANGO_DEBUG", True)
ALLOWED_HOSTS = [host.strip() for host in env("DJANGO_ALLOWED_HOSTS", "*").split(",") if host.strip()]

CSRF_TRUSTED_ORIGINS = [
    origin.strip()
    for origin in env(
        "DJANGO_CSRF_TRUSTED_ORIGINS",
        "https://*.up.railway.app,https://*.railway.app",
    ).split(",")
    if origin.strip()
]

SITE_URL = env("SITE_URL", "http://127.0.0.1:8000")
TELEGRAM_BOT_TOKEN = env("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_BOT_USERNAME = env("TELEGRAM_BOT_USERNAME", "")

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "accounts",
    "store",
    "catalog",
    "orders",
    "payment",
    "telegrambot",
    "paytechuz.integrations.django",
]

PAYTECHUZ = {
    "PAYME": {
        "PAYME_ID": env("PAYME_ID", ""),
        "PAYME_KEY": env("PAYME_KEY", ""),
        "ACCOUNT_MODEL": "payment.models.Invoice",
        "ACCOUNT_FIELD": "id",
        "AMOUNT_FIELD": "amount",
        "ONE_TIME_PAYMENT": True,
        "IS_TEST_MODE": env_bool("PAYME_TEST_MODE", True),
    },
    "CLICK": {
        "SERVICE_ID": env("CLICK_SERVICE_ID", ""),
        "MERCHANT_ID": env("CLICK_MERCHANT_ID", ""),
        "MERCHANT_USER_ID": env("CLICK_MERCHANT_USER_ID", ""),
        "SECRET_KEY": env("CLICK_SECRET_KEY", ""),
        "ACCOUNT_MODEL": "payment.models.Invoice",
        "ACCOUNT_FIELD": "id",
        "COMMISSION_PERCENT": 0.0,
        "ONE_TIME_PAYMENT": True,
        "IS_TEST_MODE": env_bool("CLICK_TEST_MODE", True),
    },
}





AUTH_USER_MODEL = "accounts.User"
AUTHENTICATION_BACKENDS = [
    "accounts.backends.PhoneBackend",
    "django.contrib.auth.backends.ModelBackend",
]
LOGIN_URL = "accounts:login"
LOGIN_REDIRECT_URL = "profile"
LOGOUT_REDIRECT_URL = "index"

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

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"

DATABASE_URL = env("DATABASE_URL")
if DATABASE_URL:
    DATABASES = {
        "default": dj_database_url.config(
            default=DATABASE_URL,
            conn_max_age=600,
            conn_health_checks=True,
        )
    }
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }

# Redis Cache configuration
REDIS_URL = env("REDIS_URL")
if REDIS_URL:
    CACHES = {
        "default": {
            "BACKEND": "django_redis.cache.RedisCache",
            "LOCATION": REDIS_URL,
            "OPTIONS": {
                "CLIENT_CLASS": "django_redis.client.DefaultClient",
            }
        }
    }
else:
    CACHES = {
        "default": {
            "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        }
    }


AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "uz"
TIME_ZONE = "Asia/Tashkent"
USE_I18N = True
USE_TZ = True

STATIC_URL = "/static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_STORAGE = (
    "django.contrib.staticfiles.storage.StaticFilesStorage"
    if DEBUG
    else "whitenoise.storage.CompressedManifestStaticFilesStorage"
)

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
USE_X_FORWARDED_HOST = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_BROWSER_XSS_FILTER = True
X_FRAME_OPTIONS = "DENY"
SESSION_COOKIE_SECURE = not DEBUG
CSRF_COOKIE_SECURE = not DEBUG

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "verbose",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": env("DJANGO_LOG_LEVEL", "INFO"),
    },
}
