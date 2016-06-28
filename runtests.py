import sys

import django
from django.conf import settings
try:
  # Django < 1.9
  from django.test.simple import DjangoTestSuiteRunner
  test_runner = DjangoTestSuiteRunner(verbosity=1)
except ImportError:
  from django.test.runner import DiscoverRunner
  test_runner = DiscoverRunner(verbosity=1)


settings.configure(DEBUG = True,
                   DATABASES = {
                     'default': {
                       'ENGINE': 'django.db.backends.sqlite3',
                     },
                   },
                   MIDDLEWARE_CLASSES = (
                      'django.contrib.sessions.middleware.SessionMiddleware',
                   ),
                   ROOT_URLCONF = 'tests.urls',
                   INSTALLED_APPS = ('django.contrib.auth',
                                     'django.contrib.contenttypes',
                                     'django.contrib.sessions',
                                     'django.contrib.admin',
                                     'lock_tokens',
                                     'tests',
                                     ))
django.setup()
failures = test_runner.run_tests(['tests',])
if failures:
    sys.exit(failures)
