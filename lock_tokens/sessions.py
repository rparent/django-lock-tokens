from django.contrib.contenttypes.models import ContentType

from lock_tokens.models import LockToken, LockableModel


def get_session_key(obj):
  contenttype = ContentType.objects.get_for_model(obj)
  return "_".join([contenttype.app_label, contenttype.model, str(obj.id)])

def lock_for_session(obj, session):
  session_key = get_session_key(obj)
  token = session.get(session_key)
  lock_token = LockableModel.lock(obj, token)
  session[session_key] = lock_token['token']

def unlock_for_session(obj, session):
  session_key = get_session_key(obj)
  token = session.get(session_key)
  LockableModel.unlock(obj, token)
  if token:
    del session[session_key]

def check_for_session(obj, session):
  session_key = get_session_key(obj)
  token = session.get(session_key)
  return LockableModel.check_lock_token(obj, token)
