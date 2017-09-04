from django.core.management.base import BaseCommand

from lock_tokens.models import LockToken
from lock_tokens.utils import get_oldest_valid_tokens_datetime


class Command(BaseCommand):

    def handle(self, *args, **opts):
        set_before = get_oldest_valid_tokens_datetime()
        expired_tokens = LockToken.objects.filter(locked_at__lt=set_before)
        n = expired_tokens.count()
        expired_tokens.delete()
        self.stdout.write(
            self.style.SUCCESS('Successfully removed %s expired tokens' % n))
