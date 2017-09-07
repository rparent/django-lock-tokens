import datetime
import warnings
from uuid import uuid4

from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import IntegrityError, models
from django.utils import timezone

from lock_tokens.exceptions import (
    AlreadyLockedError,
    LockExpiredWarning,
    NoLockWarning,
    UnlockForbiddenError
)
from lock_tokens.managers import LockableModelManager, LockTokenManager
from lock_tokens.settings import DATEFORMAT, TIMEOUT
from lock_tokens.utils import get_oldest_valid_tokens_datetime


def get_random_token():
    return uuid4().hex


class LockToken(models.Model):
    created = models.DateTimeField(auto_now_add=True, editable=False)
    token_str = models.CharField(max_length=32, unique=True, editable=False,
                                 default=get_random_token)
    locked_object_content_type = models.ForeignKey(ContentType)
    locked_object_id = models.PositiveIntegerField()
    locked_object = GenericForeignKey('locked_object_content_type',
                                      'locked_object_id')
    locked_at = models.DateTimeField(editable=False, default=timezone.now)

    objects = LockTokenManager()

    def __unicode__(self):
        return self.token_str

    def has_expired(self):
        return self.locked_at < get_oldest_valid_tokens_datetime()

    def get_expiration_datetime(self):
        return self.locked_at + datetime.timedelta(seconds=TIMEOUT)

    def renew(self):
        self.locked_at = timezone.now()
        self.save()

    def serialize(self):
        return {
            "token": self.token_str,
            "expires": datetime.datetime.strftime(self.get_expiration_datetime(),
                                                  DATEFORMAT)
        }

    def save(self, *args, **opts):
        try:
            return super(LockToken, self).save(*args, **opts)
        except IntegrityError as e:
            token = LockToken.objects.get(locked_object_id=self.locked_object_id,
                                          locked_object_content_type=self.locked_object_content_type)
            if token.has_expired():
                token.delete()
                return self.save(*args, **opts)
            raise AlreadyLockedError

    class Meta:
        unique_together = (('locked_object_content_type', 'locked_object_id'),)


class LockableModel(models.Model):

    objects = LockableModelManager()

    def _lock(self, token=None):
        lock_token, created = LockToken.objects.get_or_create_for_object(self)
        if not created:
            if lock_token.token_str == token:
                lock_token.renew()
            else:
                raise AlreadyLockedError
        return lock_token

    def _check_and_get_lock_token(self, token):
        try:
            lock_token = LockToken.objects.get_for_object(self)
        except LockToken.DoesNotExist:
            warnings.warn('This object is not locked.', NoLockWarning)
            return True, None
        if token == lock_token.token_str:
            if lock_token.has_expired():
                warnings.warn('Lock has expired', LockExpiredWarning)
            return True, lock_token
        return False, None

    def lock(self, token=None):
        lock_token = self._lock(token)
        return lock_token.serialize()

    def unlock(self, token):
        allowed, lock_token = self._check_and_get_lock_token(token)
        if not allowed:
            raise UnlockForbiddenError
        if lock_token:
            lock_token.delete()

    def check_lock_token(self, token):
        return self._check_and_get_lock_token(token)[0]

    def is_locked(self):
        try:
            lock_token = LockToken.objects.get_for_object(self)
        except LockToken.DoesNotExist:
            return False
        return not lock_token.has_expired()

    class Meta:
        abstract = True
