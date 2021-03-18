from django.contrib import admin, messages
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import PermissionDenied
from django.db.models import Count
from django.utils.translation import gettext as _

from lock_tokens.exceptions import AlreadyLockedError
from lock_tokens.sessions import (
    check_for_session,
    get_session_key,
    lock_for_session,
    unlock_for_session
)


class LockableModelAdmin(admin.ModelAdmin):
    def render_change_form(self, request, context, add=False, change=False, form_url='', obj=None):
        # use custom template in change view, but use default in add view, as lock is not used there
        self.change_form_template = 'admin/lock_tokens_change_form.html'
        if add:
            self.change_form_template = None

        return super(LockableModelAdmin, self).render_change_form(request, context, add, change,
                                                                  form_url, obj)

    def change_view(self, request, object_id, form_url="", extra_context=None):
        extra_context = extra_context or {}
        extra_context["already_locked"] = False
        obj = self.model.objects.get(id=object_id)
        try:
            # When the request has the "GET" method, it means that the view will simply
            # retrieve the object and display the form. So in this case it is ok to force
            # the generation of a new lock token, without trying to use a potential existing
            # token key in the session.
            # When the request has the "POST" method, the user is trying to modify the object.
            # So in this case, to avoid overwriting with an ivalid token, it is mandatory to
            # have a valid token in session.
            force_new_session_lock = (request.method == 'GET')
            lock_for_session(obj, request.session, force_new=force_new_session_lock)
            extra_context["lock_token"] = request.session[get_session_key(obj)]
        except AlreadyLockedError:
            messages.add_message(
                request,
                messages.ERROR,
                _("You cannot edit this object, it has been locked. Come back later.")
            )
        return super(LockableModelAdmin, self).change_view(request, object_id,
                                                           form_url, extra_context)

    def save_model(self, request, obj, form, change):
        if change:
            if not check_for_session(obj, request.session):
                raise PermissionDenied(_("Invalid lock, cannot save."))
            try:
              # Renew lock to make sure it is still valid when saving
              lock_for_session(obj, request.session)
            except AlreadyLockedError:
              # Race condition: lock expired just after the check_for_session call and
              # someone else locked the object before the lock_for_session call
              raise PermissionDenied(_("Lock has expired, cannot save."))
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
