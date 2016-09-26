from django.contrib import admin, messages
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import PermissionDenied
from django.db.models import Count

from lock_tokens.exceptions import AlreadyLockedError
from lock_tokens.models import LockToken
from lock_tokens.sessions import (check_for_session, get_session_key,
    lock_for_session, unlock_for_session)


class LockableModelAdmin(admin.ModelAdmin):

  change_form_template = 'admin/lock_tokens_change_form.html'

  def change_view(self, request, object_id, form_url="", extra_context=None):
    extra_context = extra_context or {}
    extra_context["already_locked"] = False
    obj = self.model.objects.get(id=object_id)
    try:
      lock_for_session(obj, request.session)
      extra_context["lock_token"] = request.session[get_session_key(obj)]
    except AlreadyLockedError:
      messages.add_message(request, messages.ERROR, "You cannot edit this "
          "object, it has been locked. Come back later.")
    return super(LockableModelAdmin, self).change_view(request, object_id,
        form_url, extra_context)

  def save_model(self, request, obj, form, change):
    if change:
      if not check_for_session(obj, request.session):
        raise PermissionDenied("Resource already locked, cannot save.")
    super(LockableModelAdmin, self).save_model(request, obj, form, change)
    if change:
      unlock_for_session(obj, request.session)


class LockedContentTypesFilter(admin.SimpleListFilter):

  title = 'Content Type'
  parameter_name = 'contenttype'

  def lookups(self, request, model_admin):
    return ((c.id, c.name) for c in ContentType.objects.annotate(
      nb_locks=Count('locktoken')).filter(nb_locks__gt=0))

  def queryset(self, request, queryset):
    contenttype_id = self.value()
    if contenttype_id:
      return queryset.filter(locked_object_content_type_id=contenttype_id)
    return queryset


class LockTokenAdmin(admin.ModelAdmin):

  list_display = ('token_str', 'locked_object_content_type', 'locked_object_id',
      'locked_at', 'expired', )
  list_filter = (LockedContentTypesFilter,)
  readonly_fields = ('locked_object_content_type', 'locked_object_id',
      'token_str', 'locked_at',)

  def expired(self, obj):
    return obj.has_expired()
