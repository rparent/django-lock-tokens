from django.conf.urls import url

from lock_tokens.views import LockTokenDetailView, LockTokenListView

urlpatterns = [
    url(r'^(?P<app_label>\w+)/(?P<model>\w+)/(?P<object_id>\d+)/$',
        LockTokenListView.as_view(), name='list-view'),
    url(r'^(?P<app_label>\w+)/(?P<model>\w+)/(?P<object_id>\d+)/(?P<token>\w+)/$',
        LockTokenDetailView.as_view(), name='detail-view'),
]
