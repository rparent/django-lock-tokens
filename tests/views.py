# -*- coding: utf-8
from __future__ import absolute_import

from django.http import HttpResponse

from lock_tokens.decorators import holds_lock_on_object, locks_object
from tests.models import TestModel


@locks_object(TestModel, lambda request: request.GET.get('object_id'))
def test_view_1(request):
    return HttpResponse('OK')


@locks_object(TestModel, lambda request, object_id: object_id)
def test_view_2(request, object_id):
    return HttpResponse('OK')


@holds_lock_on_object(TestModel, lambda request, object_id: object_id)
def test_view_3(request, object_id):
    return HttpResponse('OK')
