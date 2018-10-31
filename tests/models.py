# -*- coding: utf-8
from django.db import models

from lock_tokens.models import LockableModel


class TestModel(LockableModel):
    """Test model that inherits LockableModel"""
    name = models.CharField(max_length=32)


class RegularModel(models.Model):
    """Test model that does not inherit LockableModel"""
    name = models.CharField(max_length=32)
