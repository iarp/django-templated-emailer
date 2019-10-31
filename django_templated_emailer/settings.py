from django.conf import settings
from django.utils.module_loading import import_string
from django.db import models


def _setting(name, default=None):
    return getattr(settings, f'TEMPLATED_EMAILER_{name}', default)


# Whether or not to log the result of the sender task.
CELERY_IGNORE_RESULT = _setting('CELERY_TASK_SENDER_IGNORE_RESULT', False)

tmp = settings.SETTINGS_MODULE.split('.')
if len(tmp) == 1:
    project = tmp[0]
else:
    project = '.'.join(tmp[:-1])

CELERY_APP_IMPORT_PATH = _setting('CELERY_APP', f'{project}.celery.app')
try:
    PROJECT_CELERY_APP = import_string(CELERY_APP_IMPORT_PATH)
except ImportError:
    PROJECT_CELERY_APP = None

# Default model field type for Template and Queue
BODY_FIELD_TYPE = _setting('DEFAULT_BODY_FIELD_TYPE', models.TextField)

# Allow overriding Template and Queue body field types.
TEMPLATE_BODY_FIELD_TYPE = _setting('TEMPLATE_BODY_FIELD_TYPE', BODY_FIELD_TYPE)
TEMPLATE_BODY_FIELD_PARAMS = _setting('TEMPLATE_BODY_FIELD_PARAMS', {})
if isinstance(TEMPLATE_BODY_FIELD_TYPE, str):
    TEMPLATE_BODY_FIELD_TYPE = import_string(TEMPLATE_BODY_FIELD_TYPE)

QUEUE_BODY_FIELD_TYPE = _setting('QUEUE_BODY_FIELD_TYPE', BODY_FIELD_TYPE)
QUEUE_BODY_FIELD_PARAMS = _setting('QUEUE_BODY_FIELD_PARAMS', {})
if isinstance(QUEUE_BODY_FIELD_TYPE, str):
    QUEUE_BODY_FIELD_TYPE = import_string(QUEUE_BODY_FIELD_TYPE)

# Allow changing template name field where default=True?
# Setting this to true can cause EmailQueue.queue_email(template_name='...') because someone changed the name.
TEMPLATE_DEFAULT_ALLOW_CHANGING_NAME = _setting('ALLOW_DEFAULT_CHANGE_NAME', False)

# Do you want to allow deletion of default templates?
TEMPLATE_DEFAULT_ALLOW_DELETE = _setting('ALLOW_DEFAULT_DELETE', False)

# Allows projects to inject their own global variables to the context passed into subject and body.
# for example: {domain} might be your root domain of the site for linking purposes.
# MUST be of type dict, can be a function as long as it returns dict.
GLOBAL_CONTEXTS = _setting('GLOBAL_CONTEXTS', {})
if isinstance(GLOBAL_CONTEXTS, str):
    GLOBAL_CONTEXTS = import_string(GLOBAL_CONTEXTS)
if callable(GLOBAL_CONTEXTS):
    GLOBAL_CONTEXTS = GLOBAL_CONTEXTS()
if not isinstance(GLOBAL_CONTEXTS, dict):
    raise AssertionError(f'GLOBAL_CONTEXTS must be of type dict, found {type(GLOBAL_CONTEXTS)}')
