from django.contrib import admin, messages
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import PermissionDenied

from lock_tokens.exceptions import AlreadyLockedError
from lock_tokens.sessions import (check_for_session, lock_for_session,
    unlock_for_session)


class LockableModelAdmin(admin.ModelAdmin):

  change_form_template = 'admin/lock_tokens_change_form.html'

  def change_view(self, request, object_id, form_url="", extra_context=None):
    extra_context = extra_context or {}
    extra_context["already_locked"] = False
    obj = self.model.objects.get(id=object_id)
    try:
      lock_for_session(obj, request.session)
    except AlreadyLockedError:
      extra_context["already_locked"] = True
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
