========================
Django Templated Emailer
========================

Adds EmailTemplate and EmailQueue, to create and send templated emails.

I only work with Python 3.6 and 3.7 currently, as such these may not work in
previous versions. Most notably due to f-strings.

Installation
============

    pip install -e git+https://iarp@bitbucket.org/iarp/django-templated-emailer.git#egg=django_templated_emailer

Settings
========

TEMPLATED_EMAILER_CELERY_APP (='project.celery.app')
    If you use celery, this is a dot notation path to the app variable within celery.py

TEMPLATED_EMAILER_CELERY_TASK_SENDER_IGNORE_RESULT (=False)
    If using the celery task, ignore the result?

TEMPLATED_EMAILER_DEFAULT_BODY_FIELD_TYPE (=models.TextField)
    Change the default body field type used on Template and Queue

TEMPLATED_EMAILER_TEMPLATE_BODY_FIELD_TYPE (=TEMPLATED_EMAILER_DEFAULT_BODY_FIELD_TYPE)
    Change the body field type on the EmailTemplate model

TEMPLATED_EMAILER_TEMPLATE_BODY_FIELD_PARAMS (={})
    Parameters to pass to the field type upon initialization in the model

TEMPLATED_EMAILER_QUEUE_BODY_FIELD_TYPE (=TEMPLATED_EMAILER_DEFAULT_BODY_FIELD_TYPE)
    Change the body field type on the EmailQueue model

TEMPLATED_EMAILER_QUEUE_BODY_FIELD_PARAMS (={})
    Parameters to pass to the field type upon initialization in the model

TEMPLATED_EMAILER_ALLOW_DEFAULT_CHANGE_NAME (=False)
    When an EmailTemplate object has default=True, do you want to allow the Name value to change?
    When you call EmailQueue.queue_email(template_name=''), allowing someone to change the name 
    without updating your code, it will cause emails to no send...etc. This setting allows you 
    to stop someone from changing the name accidentily, if it does need changing you will need 
    to update it directly in the database to create a new EmailTemplate object. 
 
TEMPLATED_EMAILER_ALLOW_DEFAULT_DELETE (=False)
    Allow EmailTemplate objects with default=True to be deletable?
