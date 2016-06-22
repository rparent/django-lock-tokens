import warnings

from django.contrib.contenttypes.models import ContentType
from django.db.models import Manager

from lock_tokens.exceptions import (NoLockWarning, LockExpiredWarning,
    UnlockForbiddenError)
from lock_tokens.utils import get_oldest_valid_tokens_datetime


class LockTokenManager(Manager):

  def get_for_object(self, obj):
    contenttype = ContentType.objects.get_for_model(obj)
    return self.get(locked_object_content_type=contenttype,
        locked_object_id=obj.id,
        locked_at__gte=get_oldest_valid_tokens_datetime())

  def get_or_create_for_object(self, obj):
    try:
      return (self.get_for_object(obj), False)
    except self.model.DoesNotExist:
      return (self.create(locked_object=obj), True)


class LockableModelManager(Manager):

  def get_and_lock(self, *args, **kwargs):
    from lock_tokens.models import LockToken
    obj = super(LockableModelManager, self).get(*args, **kwargs)
    lock_token = LockToken.objects.create(obj)
    return obj, lock_token.serialize()
