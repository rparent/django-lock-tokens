import datetime
import sys
import threading
from types import MethodType

from django.db import models
from django.utils import timezone

from lock_tokens.settings import TIMEOUT


LESS_THAN_PYTHON3 = sys.version_info[0] < 3

def get_oldest_valid_tokens_datetime():
    return timezone.now() - datetime.timedelta(seconds=TIMEOUT)


class _LoopThread(threading.Thread):

    LOOP_TIME = max(TIMEOUT - 1, 1)

    def __init__(self, lock_token):
        self.lock_token = lock_token
        self.stop = threading.Event()
        super(_LoopThread, self).__init__(target=self.loop)

    def loop(self):
        def renew(myself):
            try:
                myself.lock_token.renew()
            except:
                myself.stop.set()
        renew(self)
        while not self.stop.wait(self.LOOP_TIME):
            renew(self)

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


def class_or_bound_method(function):
    function._bind_at_instanciation = True
    return classmethod(function)


class DLTModelProxyBase(models.base.ModelBase):

    def __call__(cls, *args, **kwargs):
        instance = super(DLTModelProxyBase, cls).__call__(*args, **kwargs)
        for key in dir(cls):
            try:
              obj = getattr(instance, key)
            except AttributeError:
              # Happens for attributes like 'objects' which are not defined for an instance
              continue
            if callable(obj) and getattr(obj, '_bind_at_instanciation', False):
                setattr(instance, key, cls._get_bound_method(obj, instance))
        return instance

    @staticmethod
    def _get_bound_method(method, instance):
        if LESS_THAN_PYTHON3:
          return MethodType(method, instance, instance.__class__)
        return MethodType(method, instance)
