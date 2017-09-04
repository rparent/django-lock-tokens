# -*- coding: utf-8 -*-
from __future__ import unicode_literals, absolute_import

from django.conf.urls import include, url

import lock_tokens.urls
from tests import views

urlpatterns = [
    url(r'^lock-tokens/', include(lock_tokens.urls, namespace='lock-tokens')),
    url(r'^test1/$', views.test_view_1, name='view-that-locks-object-1'),
    url(r'^test2/(?P<object_id>\d+)/$', views.test_view_2,
        name='view-that-locks-object-2'),
    url(r'^test3/(?P<object_id>\d+)/$', views.test_view_3,
        name='view-that-unlocks-object'),
]
