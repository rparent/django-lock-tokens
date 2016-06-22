from django.conf.urls import url

from lock_tokens.views import LockTokenAccessView, LockTokenCreateView


urlpatterns = [
    url(r'^(?P<app_label>\w+)/(?P<model>\w+)/(?P<object_id>\d+)/$',
      LockTokenCreateView.as_view(), name='create-token'),
    url(r'^(?P<app_label>\w+)/(?P<model>\w+)/(?P<object_id>\d+)/(?P<token>\w+)/$',
      LockTokenAccessView.as_view(), name='access-token'),
]
