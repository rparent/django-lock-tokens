# -*- coding: utf-8
from __future__ import absolute_import

import datetime
import time

from django.test import TransactionTestCase

from tests.models import TestModel

from lock_tokens.exceptions import AlreadyLockedError, UnlockForbiddenError
from lock_tokens.models import LockToken
from lock_tokens.settings import TIMEOUT


class LockableModelTestCase(TransactionTestCase):

    def setUp(self):
        self.test_model_instance = TestModel.objects.create(
            name='test LockableModel')

    def test_locking_scenario(self):
        # Lock object
        token_dict = self.test_model_instance.lock()
        self.assertIsInstance(token_dict, dict, "The lock method should return a "
                              "dictionary instance")
        self.assertIn('token', token_dict.keys(), "The token dictionary should "
                      "contain a 'token' key")
        self.assertIsInstance(token_dict['token'], str)
        self.assertIn('expires', token_dict.keys(), "The token dictionary should "
                      "contain a 'expires' key")
        self.assertIsInstance(token_dict['expires'], str)

        # Check that object is locked
        self.assertTrue(self.test_model_instance.is_locked(), "The is_locked method"
                        " should return True since the object is locked")

        # Try to access it without providing token
        with self.assertRaises(AlreadyLockedError, msg="Trying to lock already "
                               "locked object without valid token should raise an AlreadyLockedError"):
            self.test_model_instance.lock()
        with self.assertRaises(UnlockForbiddenError, msg="Trying to unlock already "
                               "locked object without valid token should raise an "
                               "UnlockForbiddenError"):
            self.test_model_instance.unlock('wrong_token')

        # Renew lock token for object
        time.sleep(1)
        new_token_dict = self.test_model_instance.lock(
            token=token_dict['token'])
        self.assertEqual(token_dict['token'], new_token_dict['token'], "The token "
                         "string should not have changed when renewing token")
        self.assertNotEqual(token_dict['expires'], new_token_dict['expires'], "The "
                            "token expiration date string should have changed when renewing token")
        self.test_model_instance.unlock(token=token_dict['token'])

        # Unlock object
        self.test_model_instance.unlock(token=token_dict['token'])

        # Check that the object is unlocked
        self.assertFalse(self.test_model_instance.is_locked(), "The is_locked "
                         "method should return False since the object is unlocked")

    def test_expired_lock(self):
        lock_token = self.test_model_instance._lock()
        lock_token.locked_at = lock_token.locked_at - \
            datetime.timedelta(seconds=TIMEOUT + 1)
        lock_token.save()
        # Now we have an expired lock token attached to the test model instance

        # Check if the object is considered as locked
        self.assertFalse(self.test_model_instance.is_locked(), "The is_locked "
                         "method should return False since the lock on the object has expired.")

        # Lock the object
        new_lock_token = self.test_model_instance._lock()
        self.assertNotEqual(lock_token.token_str, new_lock_token.token_str, "The "
                            "new token string should not be equal to the expired token one")
        # We check that the expired lock token has been correctly removed in db
        with self.assertRaises(LockToken.DoesNotExist):
            LockToken.objects.get(id=lock_token.id)
