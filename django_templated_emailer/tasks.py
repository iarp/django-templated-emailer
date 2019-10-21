from __future__ import absolute_import, unicode_literals

from django.core.management import call_command
from .settings import PROJECT_CELERY_APP, CELERY_IGNORE_RESULT


@PROJECT_CELERY_APP.task(bind=True, ignore_result=CELERY_IGNORE_RESULT)
def send_emailqueue_items(self):
    call_command('emailqueue_send')
