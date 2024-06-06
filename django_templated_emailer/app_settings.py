from django.utils.module_loading import import_string
from django.db import models


class AppSettings(object):

    def __init__(self, prefix=None):
        self.prefix = prefix
        if not isinstance(self.GLOBAL_CONTEXTS, dict):
            raise AssertionError(f'GLOBAL_CONTEXTS must be of type dict, found {type(self.GLOBAL_CONTEXTS)}')

    def _setting(self, name, default):
        from django.conf import settings
        return getattr(settings, self.prefix + name, default)

    @property
    def CELERY_IGNORE_RESULT(self):
        # Whether or not to log the result of the sender task
        return self._setting('CELERY_TASK_SENDER_IGNORE_RESULT', False)

    @property
    def BODY_FIELD_TYPE(self):
        # Default model field type for Template and Queue
        return self._setting('DEFAULT_BODY_FIELD_TYPE', models.TextField)

    @property
    def TEMPLATE_BODY_FIELD_TYPE(self):
        # Allow overriding Template and Queue body field types.
        ftype = self._setting('TEMPLATE_BODY_FIELD_TYPE', self.BODY_FIELD_TYPE)
        if isinstance(ftype, str):
            return import_string(ftype)
        return ftype

    @property
    def TEMPLATE_BODY_FIELD_PARAMS(self):
        return self._setting('TEMPLATE_BODY_FIELD_PARAMS', {})

    @property
    def QUEUE_BODY_FIELD_TYPE(self):
        ftype = self._setting('QUEUE_BODY_FIELD_TYPE', self.BODY_FIELD_TYPE)
        if isinstance(ftype, str):
            return import_string(ftype)
        return ftype

    @property
    def QUEUE_BODY_FIELD_PARAMS(self):
        return self._setting('QUEUE_BODY_FIELD_PARAMS', {})

    @property
    def TEMPLATE_DEFAULT_ALLOW_CHANGING_NAME(self):
        # Allow changing template name field where default=True?
        # Setting this to true can cause EmailQueue.queue_email(template_name='...') because someone changed the name.
        return self._setting('ALLOW_DEFAULT_CHANGE_NAME', False)

    @property
    def TEMPLATE_DEFAULT_ALLOW_DELETE(self):
        # Do you want to allow deletion of default templates?
        return self._setting('ALLOW_DEFAULT_DELETE', False)

    @property
    def GLOBAL_CONTEXTS(self):
        # Allows projects to inject their own global variables to the context passed into subject and body.
        # for example: {domain} might be your root domain of the site for linking purposes.
        # MUST be of type dict, can be a function as long as it returns dict.

        GLOBAL_CONTEXTS = self._setting('GLOBAL_CONTEXTS', {})
        if isinstance(GLOBAL_CONTEXTS, str):
            GLOBAL_CONTEXTS = import_string(GLOBAL_CONTEXTS)
        if callable(GLOBAL_CONTEXTS):
            GLOBAL_CONTEXTS = GLOBAL_CONTEXTS()
        return GLOBAL_CONTEXTS

app_settings = AppSettings('TEMPLATED_EMAILER_')
