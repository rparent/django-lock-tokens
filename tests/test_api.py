# -*- coding: utf-8
from __future__ import absolute_import, unicode_literals

import json
import time

from django.core.urlresolvers import reverse
from django.test import TransactionTestCase

import six

from tests.models import TestModel

from .compat import force_text


class APITestCase(TransactionTestCase):

    def assert_json_response(self, response, status_code=200,
                             msg=None, validate_content_type=True):
        self.assertEqual(status_code, response.status_code, msg)
        if validate_content_type:
            self.assertEqual('application/json',
                             response['content-type'].split(';')[0])

    def get_json_content(self, response):
        """
        GET url and return content
        """
        content = json.loads(force_text(response.content))
        return content

    def test_locking_scenario(self):
        obj = TestModel.objects.create(name='test api')
        base_url = reverse('lock-tokens:list-view', args=['tests', 'testmodel',
                                                          obj.id])

        # Lock object
        response = self.client.post(base_url)
        self.assert_json_response(
            response, 201, "The API should return HTTP 201 when lock is created")
        token_dict = self.get_json_content(response)
        self.assertIn('token', token_dict.keys(), "The token dictionary should "
                      "contain a 'token' key")
        self.assertIsInstance(token_dict['token'], six.text_type, "Wrong format for "
                              "'token' key")
        self.assertIn('expires', token_dict.keys(), "The token dictionary should "
                      "contain a 'expires' key")
        self.assertIsInstance(token_dict['expires'], six.text_type, "Wrong format for "
                              "'expires' key")

        # Retrieve token
        response = self.client.get(base_url + token_dict['token'] + '/')
        self.assert_json_response(response, 200, "API should return HTTP 200 when "
                                  "retrieving lock")
        self.assertJSONEqual(response.content, json.dumps(token_dict),
                             "Retrieved dictionary is wrong")

        # Renew token
        time.sleep(1)
        response = self.client.patch(base_url + token_dict['token'] + '/')
        self.assert_json_response(response, 200, "API should return 200 when renewing "
                                  "token")
        new_token_dict = self.get_json_content(response)
        self.assertEqual(new_token_dict['token'], token_dict['token'], "API "
                         "returned wrong token string when renewing lock")
        self.assertNotEqual(new_token_dict['expires'], token_dict['expires'], "The "
                            "token expiration date was not modified after a patch request")

        # Try to access token without a valid token
        response = self.client.get(base_url + 'invalid_token/')
        self.assert_json_response(response, 403, "API should return HTTP 403 when "
                                  "trying to access lock with wrong token string", False)

        response = self.client.patch(base_url + 'invalid_token/')
        self.assert_json_response(response, 403, "API should return HTTP 403 when "
                                  "trying to access lock with wrong token string", False)

        response = self.client.delete(base_url + 'invalid_token/')
        self.assert_json_response(response, 403, "API should return HTTP 403 when "
                                  "trying to access lock with wrong token string", False)

        # Try to lock already locked object
        response = self.client.post(base_url)
        self.assert_json_response(response, 409, "API should return HTTP 409 when "
                                  "trying to lock an already locked object")

        # Remove token
        response = self.client.delete(base_url + token_dict['token'] + '/')
        self.assert_json_response(response, 204, "API should return HTTP 204 when "
                                  "successfully deleting a lock token")

        # Check it is correctly deleted
        response = self.client.get(base_url + token_dict['token'] + '/')
        self.assert_json_response(response, 404, "API should return HTTP 403 when "
                                  "trying to access an unexisting or outdated lock", False)

        response = self.client.patch(base_url + token_dict['token'] + '/')
        self.assert_json_response(response, 404, "API should return HTTP 403 when "
                                  "trying to access an unexisting or outdated lock", False)

        response = self.client.delete(base_url + token_dict['token'] + '/')
        self.assert_json_response(response, 404, "API should return HTTP 403 when "
                                  "trying to access an unexisting or outdated lock", False)
