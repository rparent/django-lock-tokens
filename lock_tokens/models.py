import datetime
from uuid import uuid4
import warnings

from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import IntegrityError, models, transaction
from django.utils import timezone

from lock_tokens.exceptions import (
    AlreadyLockedError,
    InvalidToken,
    LockExpiredWarning,
    NoLockWarning,
    UnlockForbiddenError,
)
from lock_tokens.managers import LockableModelManager, LockTokenManager
from lock_tokens.settings import DATEFORMAT, TIMEOUT
from lock_tokens.utils import class_or_bound_method, get_oldest_valid_tokens_datetime


def get_random_token():
    return uuid4().hex


class LockToken(models.Model):
    created = models.DateTimeField(auto_now_add=True, editable=False)
    token_str = models.CharField(
        max_length=32, unique=True, editable=False, default=get_random_token
    )
    locked_object_content_type = models.ForeignKey(
        ContentType, on_delete=models.CASCADE
    )
    locked_object_id = models.PositiveIntegerField()
    locked_object = GenericForeignKey("locked_object_content_type", "locked_object_id")
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
            "expires": datetime.datetime.strftime(
                self.get_expiration_datetime(), DATEFORMAT
            ),
        }

    def save(self, *args, **opts):
        try:
            with transaction.atomic():
                if not self.pk:
                    # When creating a new token, remove existing expired tokens for the object
                    # to be locked
                    LockToken.objects.filter(
                        locked_object_id=self.locked_object_id,
                        locked_object_content_type=self.locked_object_content_type,
                        locked_at__lte=self.locked_at
                        - datetime.timedelta(seconds=TIMEOUT),
                    ).delete()
                return super(LockToken, self).save(*args, **opts)
        except IntegrityError:
            raise AlreadyLockedError

    class Meta:
        unique_together = (("locked_object_content_type", "locked_object_id"),)


class LockableModel(models.Model):

    objects = LockableModelManager()

    @staticmethod
    def _lock(obj, token=None):
        # Token renewing attempt
        if token is not None:
            try:
                lock_token = LockToken.objects.get_for_object(obj)
            except LockToken.DoesNotExist:
                raise InvalidToken
            else:
                if not lock_token.token_str == token:
                    raise InvalidToken
                lock_token.renew()
                return lock_token

        # Token creation attempt
        lock_token, created = LockToken.objects.get_or_create_for_object(obj)
        if not created:
            raise AlreadyLockedError
        return lock_token

    @staticmethod
    def _check_and_get_lock_token(obj, token):
        try:
            lock_token = LockToken.objects.get_for_object(obj)
        except LockToken.DoesNotExist:
            warnings.warn("This object is not locked.", NoLockWarning)
            return False, None
        if token == lock_token.token_str:
            if lock_token.has_expired():
                warnings.warn("Lock has expired", LockExpiredWarning)
            return True, lock_token
        return False, None

    @class_or_bound_method
    def lock(cls, obj, token=None):
        lock_token = cls._lock(obj, token)
        return lock_token.serialize()

    @class_or_bound_method
    def unlock(cls, obj, token):
        allowed, lock_token = cls._check_and_get_lock_token(obj, token)
        if not allowed:
            raise UnlockForbiddenError
        if lock_token:
            lock_token.delete()

    @class_or_bound_method
    def check_lock_token(cls, obj, token):
        return cls._check_and_get_lock_token(obj, token)[0]

    @class_or_bound_method
    def is_locked(cls, obj):
        try:
            lock_token = LockToken.objects.get_for_object(obj)
        except LockToken.DoesNotExist:
            return False
        return not lock_token.has_expired()

    class Meta:
        abstract = True
