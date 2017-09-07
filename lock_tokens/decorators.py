from django.http import HttpResponseForbidden

from lock_tokens.exceptions import AlreadyLockedError
from lock_tokens.sessions import lock_for_session, unlock_for_session
from lock_tokens.utils import LockHolder


def locks_object(model, get_object_id_fn):
    def decorator(view):
        def wrapped(request, *args, **kwargs):
            object_id = get_object_id_fn(request, *args, **kwargs)
            obj = model.objects.get(id=object_id)
            try:
                lock_for_session(obj, request.session)
            except AlreadyLockedError:
                return HttpResponseForbidden("The object you are trying to access is "
                                             "locked.")
            return view(request, *args, **kwargs)
        return wrapped
    return decorator


def holds_lock_on_object(model, get_object_id_fn):
    def decorator(view):
        def wrapped(request, *args, **kwargs):
            object_id = get_object_id_fn(request, *args, **kwargs)
            obj = model.objects.get(id=object_id)
            try:
                lock_for_session(obj, request.session)
            except AlreadyLockedError:
                return HttpResponseForbidden("The object you are trying to access is "
                                             "locked.")
            lock_holder = LockHolder(obj)
            lock_holder.start()
            try:
                response = view(request, *args, **kwargs)
            finally:
                lock_holder.stop()
            unlock_for_session(obj, request.session)
            return response
        return wrapped
    return decorator
