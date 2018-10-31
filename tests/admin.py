from __future__ import absolute_import

from django.contrib import admin
from lock_tokens.admin import LockableModelAdmin

from tests.models import RegularModel


class RegularModelAdmin(LockableModelAdmin):
  pass

admin.site.register(RegularModel, RegularModelAdmin)
