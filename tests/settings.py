import os

DEBUG = True
USE_TZ = True
TIME_ZONE = "UTC"

MIDDLEWARE = []  # from 2.0 onwards, only MIDDLEWARE is used

ROOT_URLCONF = "tests.urls"
INSTALLED_APPS = [
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sites",
    "allauth",
    "allauth.account",
    "zengo",
    "tests",
]
SITE_ID = 1

DATABASES = {
    "default": {
        "ENGINE": os.environ.get("TEST_DATABASE_ENGINE", "django.db.backends.sqlite3"),
        "NAME": os.environ.get("TEST_DATABASE_NAME", "zengo"),
        "HOST": os.environ.get("TEST_DATABASE_HOST", "localhost"),
    }
}

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "debug": True,
            "context_processors": [
                "django.contrib.auth.context_processors.auth",
                "django.template.context_processors.debug",
                "django.template.context_processors.i18n",
                "django.template.context_processors.media",
                "django.template.context_processors.static",
                "django.template.context_processors.tz",
                "django.template.context_processors.request",
            ],
        },
    }
]
SECRET_KEY = "zengo-secret-key"

# all tests should have Zendesk mocked out
ZENDESK_EMAIL = "iamaemail@example.com"
ZENDESK_TOKEN = "123123123123123123123"
ZENDESK_SUBDOMAIN = "example"

ZENGO_WEBHOOK_SECRET = "zoomzoom"
