# -*- coding: utf-8
from __future__ import unicode_literals, absolute_import

import django

DEBUG = True
USE_TZ = True

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = "o0fy)a6pmew*fe9b+^wf)96)2j8)%6oz555d7by7_(*i!b8wj8"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    }
}

ROOT_URLCONF = "tests.urls"

INSTALLED_APPS = [
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.sites",
    "django.contrib.admin",
    "lock_tokens.apps.LockTokensConfig",
    "tests",
]

SITE_ID = 1

if django.VERSION >= (1, 10):
    MIDDLEWARE = (
        "django.contrib.sessions.middleware.SessionMiddleware",
    )
else:
    MIDDLEWARE_CLASSES = (
        "django.contrib.sessions.middleware.SessionMiddleware",
    )
