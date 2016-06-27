from django.conf import settings
from django.core.urlresolvers import reverse
from django.template import Library

from lock_tokens.settings import API_CSRF_EXEMPT

register = Library()

@register.inclusion_tag('api/load_client.html')
def lock_tokens_api_client(base_api_url='/lock_tokens/'):
  context = {'csrf': True, 'base_api_url': base_api_url}
  if API_CSRF_EXEMPT:
    context['csrf'] = False
  else:
    csrf_header_name = 'X-CSRFToken'
    if hasattr(settings, 'CSRF_HEADER_NAME'):
      # If django >= 1.9
      csrf_header_name = settings.CSRF_HEADER_NAME.replace('HTTP_', '').replace('_', '-')
    context['csrf_header_name'] = csrf_header_name
  return context
