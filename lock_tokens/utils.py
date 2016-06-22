import datetime
import threading
import time

from django.utils import timezone

from lock_tokens.settings import TIMEOUT


def get_oldest_valid_tokens_datetime():
  return timezone.now() - datetime.timedelta(seconds=TIMEOUT)


class _LoopThread(threading.Thread):

  LOOP_TIME = max(TIMEOUT-1, 1)

  def __init__(self, lock_token):
    self.lock_token = lock_token
    self.stop = threading.Event()
    super(_LoopThread, self).__init__(target=self.loop)

  def loop(self):
    self.lock_token.renew()
    while not self.stop.wait(self.LOOP_TIME):
      self.lock_token.renew()

  def terminate(self):
    self.stop.set()


class LockHolder(object):

  def __init__(self, obj):
    self._obj = obj
    self._thread = None

  def _init(self):
    from lock_tokens.models import LockToken
    lock_token, _ = LockToken.objects.get_or_create_for_object(self._obj)
    self._thread = _LoopThread(lock_token)

  def start(self):
    if not self._thread:
      self._init()
    self._thread.start()

  def stop(self):
    if self._thread:
      self._thread.terminate()
      self._thread.join()

  def __del__(self):
    self.stop()
