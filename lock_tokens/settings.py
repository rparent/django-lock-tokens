from django.conf import settings

lock_tokens_settings = getattr(settings, 'LOCK_TOKENS', {})

TIMEOUT = lock_tokens_settings.get('TIMEOUT', 3600)
DATEFORMAT = lock_tokens_settings.get('DATEFORMAT', "%Y-%m-%d %H:%M:%S")
