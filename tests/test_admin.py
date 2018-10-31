# -*- coding: utf-8
from django.contrib.auth.models import User
from django.test import Client, TransactionTestCase
try:
  from django.core.urlresolvers import reverse
except ImportError:
  from django.urls import reverse

from lock_tokens.models import LockableModel
from lock_tokens.sessions import check_for_session

from tests.models import RegularModel


class LockableModelAdminTestCase(TransactionTestCase):

    def setUp(self):
        self.obj = RegularModel.objects.create(name='test instance')

        self.user1 = User.objects.create(username='user1', is_staff=True, is_superuser=True)
        self.user1.set_password('test')
        self.user1.save()

        self.user2 = User.objects.create(username='user2', is_staff=True, is_superuser=True)
        self.user2.set_password('test')
        self.user2.save()

    def test_admin_lock_scenario(self):
        # User 1 accesses admin change page for the object
        admin_page_url = reverse('admin:tests_regularmodel_change', args=[self.obj.pk])
        client1 = Client()
        self.assertTrue(client1.login(username=self.user1.username, password='test'))
        r = client1.get(admin_page_url, follow=True)
        self.assertContains(r, 'Save')
        self.assertTrue(LockableModel.is_locked(self.obj))
        self.assertTrue(check_for_session(self.obj, client1.session))

        # User 2 tries to access the change page for this object
        client2 = Client()
        self.assertTrue(client2.login(username=self.user2.username, password='test'))
        r = client2.get(admin_page_url, follow=True)
        self.assertNotContains(r, 'Save')
        self.assertTrue(LockableModel.is_locked(self.obj))
        self.assertFalse(check_for_session(self.obj, client2.session))

        # Check that user 2 cannot save
        r = client2.post(admin_page_url, {'name': 'test change'}, follow=True)
        self.assertEquals(r.status_code, 403)

        # Check that user 1 can save
        r = client1.post(admin_page_url, {'name': 'new name'}, follow=True)
        self.assertEquals(r.status_code, 200)
        self.obj.refresh_from_db()
        self.assertEqual(self.obj.name, 'new name')
        self.assertFalse(LockableModel.is_locked(self.obj))
