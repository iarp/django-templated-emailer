from django.conf import settings
from django.utils.module_loading import import_string
from django.db import models

# Whether or not to log the result of the sender task.
CELERY_IGNORE_RESULT = getattr(settings, 'TEMPLATED_EMAILER_CELERY_TASK_SENDER_IGNORE_RESULT', False)

tmp = settings.SETTINGS_MODULE.split('.')
if len(tmp) == 1:
    project = tmp[0]
else:
    project = '.'.join(tmp[:-1])

CELERY_APP_IMPORT_PATH = getattr(settings, 'TEMPLATED_EMAILER_CELERY_APP', f'{project}.celery.app')
try:
    PROJECT_CELERY_APP = import_string(CELERY_APP_IMPORT_PATH)
except ImportError:
    PROJECT_CELERY_APP = None

# Default model field type for Template and Queue
BODY_FIELD_TYPE = getattr(settings, 'TEMPLATED_EMAILER_DEFUALT_BODY_FIELD_TYPE', models.TextField())

# Allow overriding Template and Queue body field types.
TEMPLATE_BODY_FIELD_TYPE = getattr(settings, 'TEMPLATED_EMAILER_QUEUE_BODY_FIELD_TYPE', BODY_FIELD_TYPE)
QUEUE_BODY_FIELD_TYPE = getattr(settings, 'TEMPLATED_EMAILER_TEMPLATE_BODY_FIELD_TYPE', BODY_FIELD_TYPE)

# Allow changing template name field where default=True?
# Setting this to true can cause EmailQueue.queue_email(template_name='...') because someone changed the name.
TEMPLATE_DEFAULT_ALLOW_CHANGING_NAME = getattr(settings, 'TEMPLATED_EMAILER_ALLOW_DEFAULT_CHANGE_NAME', False)

# Do you want to allow deletion of default templates?
TEMPLATE_DEFAULT_ALLOW_DELETE = getattr(settings, 'TEMPLATED_EMAILER_ALLOW_DEFAULT_DELETE', False)
