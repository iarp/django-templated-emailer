# Create your tasks here
from __future__ import absolute_import, unicode_literals
from django.conf import settings

from django.core.management import call_command
from django.utils.module_loading import import_string

project = '.'.join(settings.SETTINGS_MODULE.split('.')[:-1])

project_celery_app = import_string(f'{project}.celery.app')


@project_celery_app.task(bind=True)
def send_emailqueue_items(self):
    call_command('emailqueue_send')
