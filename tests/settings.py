import os


DEBUG = True
USE_TZ = True
TIME_ZONE = "UTC"
DATABASES = {
    "default": {
        "ENGINE": os.environ.get("TEST_DATABASE_ENGINE", "django.db.backends.postgresql"),
        "HOST": os.environ.get("TEST_DATABASE_HOST", "127.0.0.1"),
    }
}
MIDDLEWARE = []  # from 2.0 onwards, only MIDDLEWARE is used

ROOT_URLCONF = "tests.urls"
INSTALLED_APPS = [
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "zengo",
    "tests",
]
SITE_ID = 1

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
