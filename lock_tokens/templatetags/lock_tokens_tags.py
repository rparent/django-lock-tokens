import uuid

from django.conf import settings
try:
    from django.urls import reverse
except ImportError:
    from django.core.urlresolvers import reverse
from django.template import Library

from lock_tokens.settings import API_CSRF_EXEMPT

register = Library()


@register.inclusion_tag('api/load_client.html')
def lock_tokens_api_client():
    # Little trick to get only the base part of the api url: we get the url for
    # list-view with random string for app_label and model, then remove the
    # unnecessary part of the url
    randomstring = uuid.uuid4().hex
    base_api_url = reverse('lock-tokens:list-view', args=[randomstring, randomstring, 1]).replace(
        '%(randstring)s/%(randstring)s/1/' % {'randstring': randomstring}, '')

    context = {'csrf': True, 'base_api_url': base_api_url}
    if API_CSRF_EXEMPT:
        context['csrf'] = False
    else:
        csrf_header_name = 'X-CSRFToken'
        if hasattr(settings, 'CSRF_HEADER_NAME'):
            # If django >= 1.9
            csrf_header_name = settings.CSRF_HEADER_NAME.replace(
                'HTTP_', '').replace('_', '-')
        context['csrf_header_name'] = csrf_header_name
    return context


@register.inclusion_tag('admin/handle_lock.html')
def admin_lock_handler(app_label, model_name, object_id, token):
    return {
        'app_label': app_label,
        'model_name': model_name,
        'object_id': object_id,
        'token': token
    }

