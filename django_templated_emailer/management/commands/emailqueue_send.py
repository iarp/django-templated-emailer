import logging

from django.core.management.base import BaseCommand

from ...models import EmailQueue

log = logging.getLogger('django_templated_emailer.emailqueue_send')


class Command(BaseCommand):
    help = 'Sends all emails queued'

    def handle(self, *args, **kwargs):

        for email in EmailQueue.objects.filter(sent=False):
            try:
                email.send()
            except:
                log.exception(str(email))
