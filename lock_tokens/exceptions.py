class AlreadyLockedError(IOError):
    pass


class UnlockForbiddenError(IOError):
    pass


class NoLockWarning(Warning):
    pass


class LockExpiredWarning(Warning):
    pass
