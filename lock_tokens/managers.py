from django.contrib.contenttypes.models import ContentType
from django.db.models import Manager

from lock_tokens.utils import get_oldest_valid_tokens_datetime


class LockTokenManager(Manager):

    def get_for_object(self, obj, allow_expired=True):
        contenttype = ContentType.objects.get_for_model(obj)
        return self.get_for_contenttype_and_id(contenttype, obj.id, allow_expired)

    def get_for_contenttype_and_id(self, contenttype, object_id, allow_expired=True):
        lookup_fields = {
            'locked_object_content_type': contenttype,
            'locked_object_id': object_id
        }
        if not allow_expired:
            lookup_fields['locked_at__gte'] = get_oldest_valid_tokens_datetime()
        return self.get(**lookup_fields)

    def get_or_create_for_object(self, obj):
        try:
            return (self.get_for_object(obj, allow_expired=False), False)
        except self.model.DoesNotExist:
            return (self.create(locked_object=obj), True)


class LockableModelManager(Manager):

    def get_and_lock(self, *args, **kwargs):
        from lock_tokens.models import LockToken
        obj = super(LockableModelManager, self).get(*args, **kwargs)
        lock_token = LockToken.objects.create(obj)
        return obj, lock_token.serialize()
