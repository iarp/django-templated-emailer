from __future__ import absolute_import, unicode_literals

from django.core.management import call_command
from .app_settings import app_settings


@app_settings.PROJECT_CELERY_APP.task(bind=True, ignore_result=app_settings.CELERY_IGNORE_RESULT)
def send_emailqueue_items(self):
    call_command('emailqueue_send')
