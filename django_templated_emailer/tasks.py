from __future__ import absolute_import, unicode_literals

from celery import shared_task
from django.core.management import call_command
from .app_settings import app_settings


@shared_task(bind=True, ignore_result=app_settings.CELERY_IGNORE_RESULT)
def send_emailqueue_items(self):
    call_command('emailqueue_send')
