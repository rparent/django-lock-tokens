from django.conf.urls import re_path

from lock_tokens.views import LockTokenDetailView, LockTokenListView


app_name = 'lock_tokens'

urlpatterns = [
    re_path(r'^(?P<app_label>\w+)/(?P<model>\w+)/(?P<object_id>\d+)/$',
        LockTokenListView.as_view(), name='list-view'),
    re_path(r'^(?P<app_label>\w+)/(?P<model>\w+)/(?P<object_id>\d+)/(?P<token>\w+)/$',
        LockTokenDetailView.as_view(), name='detail-view'),
]
