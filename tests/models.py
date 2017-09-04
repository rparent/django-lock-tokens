# -*- coding: utf-8
from django.db import models

from lock_tokens.models import LockableModel


class TestModel(LockableModel):
  name = models.CharField(max_length=32)
