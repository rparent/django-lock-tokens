import datetime
import sys
import threading

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


class ClassOrBoundMethod(object):
    def __init__(self, function):
        self.function = function

    def __get__(self, instance, klass=None):
        if not klass:
            klass = type(instance)

        def method(*args, **kwargs):
            if instance is not None:
                return self.function(klass, instance, *args, **kwargs)
            return self.function(klass, *args, **kwargs)

        return method


def class_or_bound_method(function):
    return ClassOrBoundMethod(function)
