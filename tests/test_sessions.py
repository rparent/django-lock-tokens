from __future__ import absolute_import

from django.contrib.sessions.backends.db import SessionStore
from django.core.urlresolvers import reverse
from django.test import TransactionTestCase
from django.test.client import Client

from lock_tokens.exceptions import AlreadyLockedError, UnlockForbiddenError
from lock_tokens.sessions import (check_for_session, lock_for_session,
    unlock_for_session)
from tests.models import TestModel


class SessionLockingTestCase(TransactionTestCase):

  def setUp(self):
    self.test_model_instance = TestModel.objects.create(name='test sessions')

  def test_locking_scenario(self):
    session = SessionStore()
    session.save()
    other_session = SessionStore()
    other_session.save()

    # Lock object in session
    lock_for_session(self.test_model_instance, session)

    # Check that object is locked
    self.assertTrue(self.test_model_instance.is_locked())
    self.assertTrue(check_for_session(self.test_model_instance, session))

    # Try to lock/unlock object from another session
    with self.assertRaises(AlreadyLockedError):
      lock_for_session(self.test_model_instance, other_session)
    with self.assertRaises(UnlockForbiddenError):
      unlock_for_session(self.test_model_instance, other_session)
    self.assertFalse(check_for_session(self.test_model_instance, other_session))

    # Unlock object
    unlock_for_session(self.test_model_instance, session)

    # Ensure object is unlocked
    self.assertFalse(self.test_model_instance.is_locked())
    self.assertTrue(check_for_session(self.test_model_instance, session))
    self.assertTrue(check_for_session(self.test_model_instance, other_session))

  def test_view_decorators(self):
    c = Client()

    # Call a view that locks the object
    r = c.get(reverse('view-that-locks-object-1'), {
      'object_id': self.test_model_instance.id
    })
    self.assertEqual(r.status_code, 200)
    self.assertTrue(self.test_model_instance.is_locked())

    # Call another view that locks the object (same session)
    r = c.get(reverse('view-that-locks-object-2',
      args=[self.test_model_instance.id]))
    self.assertEqual(r.status_code, 200)
    self.assertTrue(self.test_model_instance.is_locked())

    # Call a view that unlocks the object after execution
    r = c.get(reverse('view-that-unlocks-object',
      args=[self.test_model_instance.id]))
    self.assertEqual(r.status_code, 200)
    self.assertFalse(self.test_model_instance.is_locked())
