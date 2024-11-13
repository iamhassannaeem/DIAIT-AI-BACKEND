import os
from datetime import timedelta
from pathlib import Path

import environ

BASE_DIR = Path(__file__).resolve().parent.parent

env = environ.Env()

environ.Env.read_env()

DEBUG = env.bool("DEBUG", default=True)

SECRET_KEY = env.str("SECRET_KEY", default="")

# ALLOWED_HOSTS = env.list("ALLOWED_HOSTS", default=[])
ALLOWED_HOSTS = env.list(
    "ALLOWED_HOSTS", default=["192.168.99.6", "localhost", "127.0.0.1"]
)

AUTH_USER_MODEL = "authentication.User"

DJANGO_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
]

PROJECT_APPS = ["authentication", "ai_call_agent"]

THIRD_PARTY_APPS = [
    "rest_framework",
    "rest_framework_simplejwt.token_blacklist",
    "corsheaders",
]

INSTALLED_APPS = DJANGO_APPS + PROJECT_APPS + THIRD_PARTY_APPS

CORS_ALLOWED_ORIGINS = env.list("CORS_ALLOWED_ORIGINS", default=[])
CORS_ALLOW_ALL_ORIGINS = True

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "authentication.middlewares.ExceptionMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
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

DATABASES = {"default": env.db_url()}

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]

# Internationalization
LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True
STATIC_URL = "static/"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
}

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(days=30),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=30),
}

STRIPE_API_SECRET_KEY = env.str("STRIPE_API_SECRET_KEY", default="")
STRIPE_API_PUBLIC_KEY = env.str("STRIPE_API_PUBLIC_KEY", default="")

MEDIA_URL = "/media/"
MEDIA_ROOT = os.path.join(BASE_DIR, "media")


APPEND_SLASH = False
TWILIO_ACCOUNT_SID = env.str("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = env.str("TWILIO_AUTH_TOKEN")
TWILIO_PHONE_NUMBER = env.str("TWILIO_PHONE_NUMBER")

EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = env("EMAIL_HOST")
EMAIL_PORT = env("EMAIL_PORT", default=587)
EMAIL_USE_TLS = env.bool("EMAIL_USE_TLS", default=True)
EMAIL_USE_SSL = env.bool("EMAIL_USE_SSL", default=False)
EMAIL_HOST_USER = env("EMAIL_HOST_USER")
EMAIL_HOST_PASSWORD = env("EMAIL_HOST_PASSWORD")
DEFAULT_FROM_EMAIL = env("DEFAULT_FROM_EMAIL")

AWS_ACCESS_KEY_ID = env("S3_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = env("S3_SECRET_ACCESS_KEY")
AWS_S3_BUCKET_NAME = env("AWS_S3_BUCKET_NAME")


CELERY_BROKER_URL = "amqp://guest:guest@localhost//"
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TASK_SERIALIZER = "json"
# CELERY_RESULT_BACKEND = "rpc://"  # Result backend, using RabbitMQ as well
# CELERY_TIMEZONE = "UTC"


# celery -A  worker --pool=gevent --loglevel=info
STRIPE_SECRET_KEY = "sk_test_51QJZKBG1zx6NU6uvlBQsJmXxif8OqT64LdgHaIphzFWGUWhr7EXvdVXBTIGFkEecv2GYBVavPPaRA3kcI3ufxfPK00l8ngvwFV"
STRIPE_PUBLISHABLE_KEY = "pk_test_51QJZKBG1zx6NU6uvtdaq4itYhqDRDXcxrAJxlvKfIC0mOpYe9il40xio2i2ElIUEZSliaTm4wvK2s2ezwzDKrnQd00ePhLf6dg"
# Cost rates per minute
SERVER_COST = 0.02
OPENAI_COST = 0.05
DEEPGRAM_COST = 0.03
TWILIO_COST = 0.10
